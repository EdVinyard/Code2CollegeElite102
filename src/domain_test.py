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

class TestValidatedFullName(unittest.TestCase):
    def test_invalid_name(self):
        ## Arrange
        for invalid_name in [None, '', ' \t\r\n']:
            with self.subTest(invalid_name):

                ## Act & Assert
                with self.assertRaises(ValueError):
                    validated_full_name(invalid_name)

    def test_valid_name(self):
        ## Arrange
        for valid_name in ['x', 'Frank', 'x ', ' x', 'Frank the Cat']:
            with self.subTest(valid_name):

                ## Act
                actual = validated_full_name(valid_name)

                ## Assert
                self.assertEqual(valid_name, actual)

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

    def test_is_open(self):
        open_account = Account(1, 'x', USD.ZERO, None)
        self.assertTrue(open_account.is_open)

        closed_account = Account(2, 'y', USD.ZERO, FakeClock().utcnow())
        self.assertFalse(closed_account.is_open)

class FakeClock(Clock):
    def __init__(self, return_value=None):
        self.value = return_value if return_value else datetime.now(timezone.utc)

    def utcnow(self):
        return self.value

class ExpectedError(Exception):
    def __init__(self):
        super().__init__()

class TestBank(unittest.TestCase):
    def test_open_account(self):
        ## Arrange
        db = Mock(return_value=Account(1, 'x', USD.ZERO, None))
        clock = Mock(Clock)
        bank = Bank(db, clock)

        ## Act
        actual = bank.open_account('Frank the Cat')

        ## Assert
        self.assertTrue(db.insert.called)
        self.assertEqual('Frank the Cat', db.insert.call_args[0][0].full_name)

    def test_open_account_db_error(self):
        ## Arrange
        db = MagicMock(side_effect=RuntimeError('fake error'))
        db.commit_transaction.side_effect = ExpectedError()
        clock = Mock(Clock)
        bank = Bank(db, clock)

        ## Act
        with self.assertRaises(ExpectedError):
            bank.open_account('Frank the Cat')

        ## Assert
        self.assertTrue(db.start_serializable_transaction.called)
        self.assertTrue(db.insert.called)
        self.assertTrue(db.commit_transaction.called)
        self.assertTrue(db.rollback_transaction.called)

    def test_load(self):
        ## Arrange
        db = Mock(return_value=Account(1, 'x', USD.ZERO, None))
        clock = Mock(Clock)
        bank = Bank(db, clock)

        ## Act
        actual = bank.load(1)

        ## Assert
        self.assertTrue(db.select_by_id.called)
        self.assertEqual(1, db.select_by_id.call_args[0][0])

    def test_close_account_with_zero_balance(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        clock = FakeClock(utcnow)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, None)
        bank = Bank(db, clock)

        ## Act
        actual = bank.close_account(1)

        ## Assert
        self.assertTrue(db.update_closed_at.called)
        self.assertEqual(1, db.update_closed_at.call_args[0][0])
        self.assertEqual(utcnow, db.update_closed_at.call_args[0][1])

    def test_close_account_with_positive_balance(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        clock = FakeClock(utcnow)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD(1_00), None)
        bank = Bank(db, clock)

        ## Act
        with self.assertRaises(ValueError):
            bank.close_account(1)

        self.assertFalse(db.update_closed_at.called)

    def test_close_account_already_closed(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        clock = FakeClock(utcnow)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, utcnow)
        bank = Bank(db, clock)

        ## Act
        bank.close_account(1)

        ## Assert
        self.assertFalse(db.update_closed_at.called)

    def test_close_account_db_error(self):
        ## Arrange
        db = MagicMock(side_effect=RuntimeError('fake error'))
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, None)
        db.commit_transaction.side_effect = ExpectedError()
        clock = Mock(Clock)
        bank = Bank(db, clock)

        ## Act
        with self.assertRaises(ExpectedError):
            bank.close_account(1)

        ## Assert
        self.assertTrue(db.start_serializable_transaction.called)
        self.assertTrue(db.update_closed_at.called)
        self.assertTrue(db.commit_transaction.called)
        self.assertTrue(db.rollback_transaction.called)

    def test_alter_name_with_open_account(self):
        ## Arrange
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, None)
        bank = Bank(db, Mock(Clock))

        ## Act
        actual = bank.alter_name(1, 'Frank the Cat')

        ## Assert
        self.assertTrue(db.update_name.called)
        self.assertEqual(1, db.update_name.call_args[0][0])
        self.assertEqual('Frank the Cat', db.update_name.call_args[0][1])

    def test_alter_name_with_closed_account(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, utcnow)
        bank = Bank(db, Mock(Clock))

        ## Act & Assert
        with self.assertRaises(ValueError):
            bank.alter_name(1, 'Frank the Cat')

        ## Assert
        self.assertFalse(db.update_name.called)

    def test_alter_name_with_invalid_name(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, None)
        bank = Bank(db, Mock(Clock))

        ## Act & Assert
        with self.assertRaises(ValueError):
            bank.alter_name(1, ' \t\r\n') ## just a bunch of whitespace

        ## Assert
        self.assertFalse(db.update_name.called)

    def test_alter_name_db_error(self):
        ## Arrange
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, None)
        db.commit_transaction.side_effect = ExpectedError()
        bank = Bank(db, Mock(Clock))

        ## Act
        with self.assertRaises(ExpectedError):
            bank.alter_name(1, 'Frank the Cat')

        ## Assert
        self.assertTrue(db.start_serializable_transaction.called)
        self.assertTrue(db.update_name.called)
        self.assertTrue(db.commit_transaction.called)
        self.assertTrue(db.rollback_transaction.called)

    def test_deposit_happy_path(self):
        ## Arrange
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD(1_00), None)
        bank = Bank(db, Mock(Clock))

        ## Act
        actual = bank.deposit(1, USD(2_00))

        ## Assert
        db.assert_has_calls([
            call.start_serializable_transaction(),
            call.select_by_id(1),
            call.update_balance(1, USD(3_00)),
            call.select_by_id(1),
            call.commit_transaction(),
            ])

    def test_deposit_into_closed_account(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, utcnow)
        bank = Bank(db, Mock(Clock))

        ## Act & Assert
        with self.assertRaises(ValueError):
            bank.deposit(1, USD(2_00))

    def test_deposit_db_error(self):
        ## Arrange
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, None)
        db.commit_transaction.side_effect = ExpectedError()
        bank = Bank(db, Mock(Clock))

        ## Act
        with self.assertRaises(ExpectedError):
            bank.deposit(1, USD(1))

        ## Assert
        self.assertTrue(db.start_serializable_transaction.called)
        self.assertTrue(db.update_balance.called)
        self.assertTrue(db.commit_transaction.called)
        self.assertTrue(db.rollback_transaction.called)

    def test_withdraw_happy_path(self):
        ## Arrange
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD(1_00), None)
        bank = Bank(db, Mock(Clock))

        ## Act
        actual = bank.withdraw(1, USD(1_00))

        ## Assert
        db.assert_has_calls([
            call.start_serializable_transaction(),
            call.select_by_id(1),
            call.update_balance(1, USD.ZERO),
            call.select_by_id(1),
            call.commit_transaction(),
            ])

    def test_withdraw_from_closed_account(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD.ZERO, utcnow)
        bank = Bank(db, Mock(Clock))

        ## Act & Assert
        with self.assertRaises(ValueError):
            bank.withdraw(1, USD(2_00))

    def test_withdraw_overdraft(self):
        ## Arrange
        utcnow = datetime.now(timezone.utc)
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD(1_00), None)
        bank = Bank(db, Mock(Clock))

        ## Act & Assert
        with self.assertRaises(ValueError):
            bank.withdraw(1, USD(2_00))

    def test_withdraw_db_error(self):
        ## Arrange
        db = MagicMock(BankDatabase)
        db.select_by_id.return_value = Account(1, 'x', USD(1), None)
        db.commit_transaction.side_effect = ExpectedError()
        bank = Bank(db, Mock(Clock))

        ## Act
        with self.assertRaises(ExpectedError):
            bank.withdraw(1, USD(1))

        ## Assert
        self.assertTrue(db.start_serializable_transaction.called)
        self.assertTrue(db.update_balance.called)
        self.assertTrue(db.commit_transaction.called)
        self.assertTrue(db.rollback_transaction.called)

if __name__ == '__main__':
    unittest.main()
