import blockcypher.api

from .utils import *
from .models import Address
from .serializers import AddressSerializer

from datetime import timedelta, datetime
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from caseStudy import settings
import json
from bit.network import get_fee

from rest_framework.decorators import api_view
from rest_framework.response import Response


@require_POST
def get_transaction_data(request):
    data = json.loads(request.body)
    source_address = (data.get('from_address'))
    to_address = (data.get('to_address'))
    amount = is_valid_amount(data.get('amount'))
    if not amount:
        return JsonResponse({"status": "error", "message": "Invalid amount"})

    if not is_valid_bitcoin_address(to_address) or not is_valid_bitcoin_address(source_address):
        return JsonResponse({"status": "error", "message": "Invalid input type"})

    balance = get_source_balance(source_address)

    # Ensure you have enough balance in the fetched UTXOs
    total_utxo_balance = balance
    if total_utxo_balance + get_fee() < amount:
        return JsonResponse({"status": "error", "message": "Insufficient balance"})

    hsh = generate_unsigned_transaction(source_address, amount, to_address)

    return JsonResponse({"status": "success", 'message': hsh})


@require_POST
def broadcast_signed_transaction(request):
    # validate
    data = json.loads(request.body)

    signed_tx = data.get('signed_tx')

    if not signed_tx:
        print("Missing signed transaction data")
        return JsonResponse({"status": "error", "message": "Missing signed transaction data"})

    if not is_valid_signed_transaction(signed_tx):
        print("Invalid signed transaction")
        return JsonResponse({"status": "error", "message": "Invalid signed transaction"})

    try:
        # Broadcast the signed transaction to the network
        if not blockcypher.pushtx(signed_tx, coin_symbol=config('COIN_SYMBOL'),
                                  api_key=settings.BLOCKCYPHER_API_KEY):
            print("Error broadcasting the transaction")
            return JsonResponse({"status": "error", "message": "Error broadcasting the transaction"})
        hash = get_txid_from_signed_transaction(signed_tx)
        return JsonResponse({"status": "success", "tx_details": hash})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error", "message": "Error broadcasting the transaction"})


@require_POST
def get_confirmations(request):
    data = json.loads(request.body)
    tx_hash = data.get('hash')

    if not tx_hash:
        return JsonResponse({"status": "error", "message": "Missing transaction hash"})

    if not is_valid_tx_hash(tx_hash):
        return JsonResponse({"status": "error", "message": "Invalid transaction hash"})

    try:
        confirmations = blockcypher.get_num_confirmations(tx_hash, coin_symbol=config('COIN_SYMBOL'))
        print(confirmations)
        return JsonResponse({"status": "success", "confirmations": confirmations})

    except blockcypher.api.RateLimitError:
        return JsonResponse({"status": "error", "message": "API rate limit exceeded. Please try again later."})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error", "message": "Error getting confirmations"})


@api_view(['GET'])
def get_addresses(request):
    all_addresses = Address.objects.all()
    serializer = AddressSerializer(all_addresses, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_address(request):
    address = request.data.get('address')
    try:
        if not validate_address(address):
            return Response({"success": False, "message": "Invalid address"})
    except AssertionError as e:
        print(e)
        return Response({"success": False, "message": "Invalid address"})
    address_fields = fetch_new_data_for_address(address)
    try:
        Address.objects.get(address=address)
        return Response({"success": False, "message": "Address already exists!"})
    except Address.DoesNotExist:
        pass
    Address.objects.create(**address_fields)
    return Response({"success": True, "message": "Address added successfully."})


@api_view(['GET'])
def get_address_details(request, bookId):
    try:
        try:
            if not validate_address(bookId):
                return Response({"success": False, "message": "Invalid address"})
        except AssertionError as e:
            print(e)
            return Response({"success": False, "message": "Invalid address"})
        book = Address.objects.get(address=bookId)

        if datetime.now(timezone.utc) - book.created_at > timedelta(minutes=30):
            new_data = fetch_new_data_for_address(bookId)
            setattr(book, "created_at", datetime.now(timezone.utc))
            for key, value in new_data.items():
                setattr(book, key, value)
            book.save()

        serializer = AddressSerializer(book)
        return Response(serializer.data)
    except Address.DoesNotExist as e:
        print(e)
        return Response({"error": "Address not found"}, status=404)
    except AssertionError as e:
        print(e)
        return Response({"error": "Address not valid"}, status=404)
