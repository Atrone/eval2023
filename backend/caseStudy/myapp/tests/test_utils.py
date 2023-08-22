from django.test import TestCase
from unittest.mock import patch, Mock
from ..views import (
    validate_address,
    first_fit_utxo_selection,
    is_valid_bitcoin_address,
    is_valid_bitcoin_address_format,
    is_valid_amount,
    is_valid_signed_transaction,
    is_valid_tx_hash
)

# Mock data
mock_unspent = [
    Mock(amount=100),
    Mock(amount=200),
    Mock(amount=300),
    Mock(amount=500)
]


class TestUtils(TestCase):

    def test_validate_address_valid(self):
        with patch("blockcypher.utils.is_valid_address_for_coinsymbol", return_value=True):
            self.assertTrue(validate_address("validAddress"))

    def test_validate_address_invalid(self):
        with patch("blockcypher.utils.is_valid_address_for_coinsymbol", return_value=False):
            with self.assertRaises(AssertionError):
                validate_address("invalidAddress")

    def test_first_fit_utxo_selection(self):
        result = first_fit_utxo_selection(mock_unspent, 500)
        self.assertEqual(result.amount, 500)

    def test_is_valid_bitcoin_address(self):
        with patch("blockcypher.utils.is_valid_address_for_coinsymbol", return_value=True):
            self.assertTrue(is_valid_bitcoin_address("validAddress"))

    def test_is_valid_bitcoin_address_format_valid(self):
        self.assertTrue(is_valid_bitcoin_address_format("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"))

    def test_is_valid_bitcoin_address_format_invalid(self):
        self.assertFalse(is_valid_bitcoin_address_format("invalidAddress"))

    def test_is_valid_amount_valid(self):
        self.assertEqual(is_valid_amount("5.0"), 5.0)

    def test_is_valid_amount_invalid(self):
        self.assertFalse(is_valid_amount("invalid"))

    def test_is_valid_signed_transaction_valid(self):
        self.assertTrue(is_valid_signed_transaction("validTransaction"))

    def test_is_valid_tx_hash_valid(self):
        self.assertTrue(is_valid_tx_hash("a" * 64))

    def test_is_valid_tx_hash_invalid(self):
        self.assertFalse(is_valid_tx_hash("invalid"))
