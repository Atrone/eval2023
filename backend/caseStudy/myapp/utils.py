import re
import blockcypher
from bit.network import NetworkAPI
from bitcoin.core import CTransaction, ValidationError
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
