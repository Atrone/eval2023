import re
from datetime import timedelta, datetime

import blockcypher
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from caseStudy import settings
import json
from bit.network import get_fee
from bit.network import NetworkAPI
from .serializers import AddressSerializer
from bitcoin.core import CTransaction, ValidationError

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Address
from decouple import config
from bitcoin import deserialize


def get_txid_from_signed_transaction(signed_hex):
    tx_data = deserialize(signed_hex)
    try:
        tx_id = tx_data['ins'][0]['outpoint']['hash']
    except Exception as e:
        print(e)
        raise KeyError("There is something wrong with the signed transaction")
    return tx_id



def validate_address(address):
    try:
        return blockcypher.utils.is_valid_address_for_coinsymbol(address, coin_symbol=config('COIN_SYMBOL'))
    except AssertionError as e:
        print(e)
        raise AssertionError("Invalid")


def first_fit_utxo_selection(unspent, required_amount):
    """
    This function implements the First Fit algorithm for UTXO selection.
    It selects UTXOs sequentially until the required amount is reached or exceeded.
    """
    total_input = 0
    selected_utxo = None

    for utxo in unspent:
        total_input += utxo.amount
        if total_input >= required_amount:
            selected_utxo = utxo
            break

    return selected_utxo


def generate_unsigned_transaction(source_address, amount_in_btc, to_address):
    unspent = NetworkAPI.get_unspent_testnet(source_address)
    amount_in_satoshis = int(amount_in_btc * 100000000)  # 1 BTC = 100,000,000 satoshis
    tx_input = first_fit_utxo_selection(unspent, amount_in_satoshis)
    tx_id = tx_input.txid
    tx_output_n = tx_input.txindex

    tx_hex = (NetworkAPI.get_transaction_by_id_testnet(tx_input.txid))

    return tx_id, tx_output_n, tx_hex, to_address, amount_in_satoshis


def is_valid_bitcoin_address(address):
    if not is_valid_bitcoin_address_format(address) or not blockcypher.utils.is_valid_address_for_coinsymbol(address,
                                                                                                             coin_symbol=config(
                                                                                                                 'COIN_SYMBOL')):
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
        print(e)
        return False


def get_source_balance(source_address):
    return blockcypher.get_address_details(source_address, coin_symbol=config('COIN_SYMBOL'))['final_balance']


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


def is_valid_signed_transaction(hex_signed_transaction):
    try:
        tx = CTransaction.deserialize(bytes.fromhex(hex_signed_transaction))

        if len(tx.vin) == 0:
            return False

        for txin in tx.vin:
            if len(txin.scriptSig) == 0:
                return False

        return True
    except (ValidationError, ValueError) as e:
        print(e)
        return False


@require_POST
def broadcast_signed_transaction(request):
    # validate
    data = json.loads(request.body)

    signed_tx = data.get('signed_tx')

    if not signed_tx:
        return JsonResponse({"status": "error", "message": "Missing signed transaction data"})

    if not is_valid_signed_transaction(signed_tx):
        return JsonResponse({"status": "error", "message": "Invalid signed transaction"})

    try:
        # Broadcast the signed transaction to the network
        if not blockcypher.pushtx(signed_tx, coin_symbol=config('COIN_SYMBOL'),
                                  api_key=settings.BLOCKCYPHER_API_KEY):
            return JsonResponse({"status": "error", "message": "Error broadcasting the transaction"})
        hash = get_txid_from_signed_transaction(signed_tx)
        return JsonResponse({"status": "success", "tx_details": hash})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error", "message": "Error broadcasting the transaction"})


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


def fetch_new_data_for_address(bookId):
    address_details = blockcypher.get_address_details(address=bookId, coin_symbol=config('COIN_SYMBOL'))
    address_fields = {key: val for key, val in address_details.items() if key not in ['txrefs', 'unconfirmed_txrefs']}
    return address_fields


def is_valid_tx_hash(tx_hash):
    # Check if the length is 64 characters
    if len(tx_hash) != 64:
        return False

    # Check if it's a valid hexadecimal
    try:
        int(tx_hash, 16)
        return True
    except ValueError as e:
        print(e)
        return False


@require_POST
def get_confirmations(request):
    data = json.loads(request.body)
    tx_hash = data.get('hash')

    if not tx_hash:
        return JsonResponse({"status": "error", "message": "Missing transaction hash"})

    if not is_valid_tx_hash(tx_hash):
        return JsonResponse({"status": "error", "message": "Invalid transaction hash"})

    try:
        return JsonResponse({"status": "success", "confirmations": blockcypher.get_num_confirmations(tx_hash,
                                                                                                     coin_symbol=config(
                                                                                                         'COIN_SYMBOL'))})

    except blockcypher.APIRateLimitExceeded:
        return JsonResponse({"status": "error", "message": "API rate limit exceeded. Please try again later."})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error", "message": "Error getting confirmations"})
