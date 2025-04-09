import unittest
from unittest.mock import MagicMock, Mock, call
from datetime import timezone

from domain import *

class TestUSD(unittest.TestCase):
    def test_positive_value(self):
        money = USD(1234)

        self.assertEqual(money.total_cents, 1234)
        self.assertEqual(money._dollars, 12)
        self.assertEqual(money._cents, 34)
        self.assertEqual(money._sign, 1)
        self.assertEqual(str(money), '$12.34')

    def test_negative_value(self):
        money = USD(-1234)

        self.assertEqual(money.total_cents, -1234)
        self.assertEqual(money._dollars, -12)
        self.assertEqual(money._cents, -34)
        self.assertEqual(money._sign, -1)
        self.assertEqual(str(money), '$-12.34')

    def test_zero(self):
        money = USD.ZERO

        self.assertEqual(money.total_cents, 0)
        self.assertEqual(money._dollars, 0)
        self.assertEqual(money._cents, 0)
        self.assertEqual(money._sign, 1)
        self.assertEqual(str(money), '$0.00')

    def test_str_edge_cases(self):
        self.assertEqual(str(USD.ZERO), '$0.00')
        self.assertEqual(str(USD(1_00)), '$1.00')
        self.assertEqual(str(USD(1_01)), '$1.01')

    def test_str_thousands_separator(self):
        self.assertEqual(str(USD(1234567890)), '$12,345,678.90')

    def test_eq(self):
        self.assertEqual(USD(-1), USD(-1))
        self.assertEqual(USD(0), USD(0))
        self.assertEqual(USD(1), USD(1))

        self.assertNotEqual(USD(0), USD(1))
        self.assertNotEqual(USD(1), USD(0))

        class CAD:
            def __init__(self, total_cents):
                self._total_cents = total_cents

        with self.assertRaises(NotImplementedError):
            if USD(1) == CAD(1):
                raise RuntimeError('something is very wrong')

    def test_max(self):
        ok = USD(USD.MAX_CENTS)

        with self.assertRaises(ValueError):
            USD(USD.MAX_CENTS + 1)

    def test_min(self):
        ok = USD(USD.MIN_CENTS)

        with self.assertRaises(ValueError):
            USD(USD.MIN_CENTS - 1)

    def test_add(self):
        self.assertEqual(USD(3_00), USD(1_00) + USD(2_00))

        with self.assertRaises(NotImplementedError):
            USD(1_00) + 1_000_000

    def test_subtract(self):
        self.assertEqual(USD(-1_00), USD(1_00) - USD(2_00))

        with self.assertRaises(NotImplementedError):
            USD(1_00) - 1_000_000

    def test_less_than(self):
        self.assertLess(USD(1_00), USD(2_00))

        with self.assertRaises(NotImplementedError):
            if USD(1_00) < 1_000_000:
                self.fail('SHOULD NOT COMPARE USD TO NUMBER')

    def test_greater_than_or_equal_to(self):
        self.assertGreaterEqual(USD(2_00), USD(1_00))

        with self.assertRaises(NotImplementedError):
            if USD(1_00) >= 1_000_000:
                self.fail('SHOULD NOT COMPARE USD TO NUMBER')

class TestAccount(unittest.TestCase):
    def test_invalid_names(self):
        for invalid_name in [None, '', ' \t\r\n']:
            with self.subTest(invalid_name):
                with self.assertRaises(ValueError):
                    Account.new(invalid_name)

    def test_closed_at_none(self):
        ## Act
        actual = Account(1, 'Frank the Cat', USD.ZERO, None)

        ## Assert
        self.assertIsNone(actual.closed_at)

    def test_closed_at_without_tzinfo(self):
        ## Arrange
        no_tzinfo = datetime(2025, 4, 5, 11, 18, 12, tzinfo=None)

        ## Act & Assert
        with self.assertRaises(ValueError):
            Account(1, 'Frank the Cat', USD.ZERO, no_tzinfo)

    def test_happy_path(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)

        ## Act
        actual = Account(12, 'Frank the Cat', USD(1_23), utcnow)

        ## Assert
        self.assertEqual(12, actual.id)
        self.assertEqual('Frank the Cat', actual.full_name)
        self.assertEqual(USD(1_23), actual.balance)
        self.assertEqual(utcnow, actual.closed_at)

if __name__ == '__main__':
    unittest.main()
