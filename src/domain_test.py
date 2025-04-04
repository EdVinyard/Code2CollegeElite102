import unittest

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

class TestAccount(unittest.TestCase):
    def test_more(self):
        self.fail('write more tests')

class TestBank(unittest.TestCase):
    def test_more(self):
        self.fail('write more tests')

if __name__ == '__main__':
    unittest.main()
