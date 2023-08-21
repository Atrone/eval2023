import re
from datetime import timedelta, datetime

import blockcypher
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from caseStudy import settings
import json
from bit.network import get_fee
from bit.network import NetworkAPI
from .serializers import AddressSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Address


def validate_address(address):
    try:
        assert blockcypher.utils.is_valid_address_for_coinsymbol(address, coin_symbol='btc-testnet')
        return True, "Valid"
    except AssertionError:
        return False, "Invalid"


def generate_unsigned_transaction(source_address, amount_in_btc, to_address):
    # Convert the public key to a Bitcoin address
    unspent = NetworkAPI.get_unspent_testnet(source_address)  # Use 'btc' for mainnet
    tx_input = unspent[0]  # make sure to grab the last unspent, or not this at least
    tx_id = tx_input.txid
    tx_output_n = tx_input.txindex

    tx_hex = (NetworkAPI.get_transaction_by_id_testnet(tx_input.txid))
    # Assuming you'd use the first unspent tx
    amount_in_satoshis = int(amount_in_btc * 100000000)  # 1 BTC = 100,000,000 satoshis

    return tx_id, tx_output_n, tx_hex, "", amount_in_satoshis, source_address, to_address, "", ""


def is_valid_bitcoin_address(address):
    if not is_valid_bitcoin_address_format(address) or not blockcypher.utils.is_valid_address_for_coinsymbol(address,
                                                                                                             coin_symbol='btc-testnet'):
        return False
    return True


def is_valid_bitcoin_address_format(address):
    pattern = re.compile(r"^[123mn][a-km-zA-HJ-NP-Z1-9]{25,34}$")
    if pattern.match(address):
        return True
    return False


def is_valid_amount(amount):
    try:
        sanitized_amount = float(amount)
        return sanitized_amount
    except ValueError as e:
        return False


def get_source_balance(source_address):
    return blockcypher.get_address_details(source_address, coin_symbol='btc-testnet')['final_balance']


@require_POST
def get_transaction_data(request):
    data = json.loads(request.body)
    source_address = (data.get('from_address'))  # in the request
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
    # sanitize
    data = json.loads(request.body)

    signed_tx = data.get('signed_tx')

    if not signed_tx:
        return JsonResponse({"status": "error", "message": "Missing signed transaction data"})

    try:
        # Broadcast the signed transaction to the network
        tx_details = blockcypher.pushtx(signed_tx, coin_symbol='btc-testnet',
                                        api_key=settings.BLOCKCYPHER_API_KEY)
        return JsonResponse({"status": "success", "tx_details": tx_details})

    except blockcypher.APIRateLimitExceeded:
        return JsonResponse({"status": "error", "message": "API rate limit exceeded. Please try again later."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": "Error broadcasting the transaction"})


@api_view(['GET'])
def get_addresses(request):
    all_addresses = Address.objects.all()
    serializer = AddressSerializer(all_addresses, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_address(request):
    address = request.data.get('address')
    assert validate_address(address)
    is_valid, validation_message = validate_address(address)
    address_fields = fetch_new_data_for_address(address)
    try:
        Address.objects.get(address=address)
        return Response({"success": False, "message": "Already exists!"})
    except Address.DoesNotExist:
        pass

    if not is_valid:
        return Response({"success": False, "message": validation_message})

    Address.objects.create(**address_fields)
    return Response({"success": True, "message": "Address added successfully."})


@api_view(['GET'])
def get_address_details(request, bookId):
    try:
        assert validate_address(bookId)
        book = Address.objects.get(address=bookId)

        if datetime.now(timezone.utc) - book.created_at > timedelta(minutes=30):
            new_data = fetch_new_data_for_address(bookId)
            setattr(book, "created_at", datetime.now(timezone.utc))
            for key, value in new_data.items():
                setattr(book, key, value)
            book.save()

        serializer = AddressSerializer(book)
        return Response(serializer.data)
    except Address.DoesNotExist:
        return Response({"error": "Address not found"}, status=404)
    except AssertionError:
        return Response({"error": "Address not valid"}, status=404)


def fetch_new_data_for_address(bookId):
    address_details = blockcypher.get_address_details(address=bookId, coin_symbol='btc-testnet')
    address_fields = {key: val for key, val in address_details.items() if key not in ['txrefs', 'unconfirmed_txrefs']}
    return address_fields

# blockcypher.get_num_confirmations() <- poll
