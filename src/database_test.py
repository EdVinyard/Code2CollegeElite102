from datetime import timedelta
from time import sleep
import unittest
from threading import Thread, current_thread
from mysql.connector import errorcode

from domain import *
from database import *

DEBUG = False

class WaitSignal:
    def __init__(self):
        self.waiting = True
    def go(self):
        self.waiting = False
    def __bool__(self):
        return self.waiting
    def for_it(self, timeout: timedelta):
        start = datetime.now()
        deadline = start + timeout

        while self.waiting and datetime.now() < deadline:
            sleep(0.001) ## seconds

        elapsed = datetime.now() - start
        tprint(f'slept for {elapsed}')
        if elapsed >= timeout:
            tprint(f'timeout occurred')

def tprint(*args, **kwargs):
    if not DEBUG:
        return

    head, *tail = args
    format = current_thread().name + ': ' + repr(args[0])
    print(format, *tail, **kwargs)

ONE_SECOND = timedelta(seconds=1)
class TestBankMySqlDatabase(unittest.TestCase):
    def test_insert_with_id(self):
        with BankMySqlDatabase() as db:
            frank = Account(1, 'Frank the Cat', USD(123_45), None)

            ## Act & Assert
            with self.assertRaises(ValueError):
                db.insert(frank)

    def test_insert_select_round_trip(self):
        ## Arrange
        with BankMySqlDatabase() as db:
            now = datetime.now(timezone.utc)
            expected = Account(None, 'Frank the Cat', USD(123_45), now)

            ## Act
            inserted = db.insert(expected)
            selected = db.select_by_id(inserted.id)

            ## Assert
            self.assertEqual(inserted.id, selected.id)

            for actual in [inserted, selected]:
                self.assertEqual(expected.full_name, actual.full_name)
                self.assertEqual(expected.balance,   actual.balance)
                self.assertEqual(expected.closed_at, actual.closed_at)

    def test_update_closed_at(self):
        ## Arrange
        with BankMySqlDatabase() as db:
            closed_at = datetime.now(timezone.utc)
            frank = db.insert(Account(None, 'Frank the Cat', USD.ZERO, None))

            ## Act
            db.update_closed_at(frank.id, closed_at)

            ## Assert
            actual = db.select_by_id(frank.id)
            self.assertEqual(frank.id,          actual.id)
            self.assertEqual(frank.full_name,   actual.full_name)
            self.assertEqual(frank.balance,     actual.balance)
            self.assertEqual(closed_at,         actual.closed_at)

    def test_update_name(self):
        ## Arrange
        with BankMySqlDatabase() as db:
            frank = db.insert(Account(None, 'Frank the Cat', USD.ZERO, None))

            ## Act
            db.update_name(frank.id, 'Frank the AMAZING Cat')

            ## Assert
            actual = db.select_by_id(frank.id)
            self.assertEqual(frank.id,                  actual.id)
            self.assertEqual('Frank the AMAZING Cat',   actual.full_name)
            self.assertEqual(frank.balance,             actual.balance)
            self.assertEqual(frank.closed_at,           actual.closed_at)

    def test_update_balance(self):
        ## Arrange
        with BankMySqlDatabase() as db:
            frank = db.insert(Account(None, 'Frank the Cat', USD.ZERO, None))
            one_dollar = USD(1_00)

            ## Act
            db.update_balance(frank.id, one_dollar)

            ## Assert
            actual = db.select_by_id(frank.id)
            self.assertEqual(frank.id,          actual.id)
            self.assertEqual(frank.full_name,   actual.full_name)
            self.assertEqual(one_dollar,        actual.balance)
            self.assertEqual(frank.closed_at,   actual.closed_at)

    def test_serializable_transaction(self):
        '''
        Frank, who has only $1.00, attempts to withdraw almost a dollar from two
        different bank branches simultaneously.
        '''
        ## Arrange
        with BankMySqlDatabase() as arrange:
            frank = arrange.insert(Account(None, 'Frank the Cat', USD(1_00), None))

        ## Act
        wait_signal = WaitSignal()
        north_branch = Thread(target=withdraw(frank.id, USD(99), wait_signal))
        south_branch = Thread(target=withdraw(frank.id, USD(98), wait_signal))

        north_branch.start()
        south_branch.start()
        wait_signal.go()

        north_branch.join()
        south_branch.join()

        ## Assert
        with BankMySqlDatabase() as azzert:
            actual = azzert.select_by_id(frank.id)
            ## Either thread may "win" the race to withdraw money,
            ## but only one should alter the row.
            self.assertGreater(USD(1_00), actual.balance)
            self.assertLess(USD.ZERO, actual.balance)

def withdraw(account_id: AccountId, withdrawal: USD, wait: WaitSignal) -> None:
    def withdraw_closure():
        with BankMySqlDatabase() as db:
            try:
                db.start_serializable_transaction()

                before = db.select_by_id(account_id)
                tprint(f'before: {before}')

                if before.balance >= withdrawal:
                    tprint(f'balance {before.balance} >= withdrawal {withdrawal}')
                else:
                    raise ValueError(f'balance {before.balance} < withdrawal {withdrawal}')

                wait.for_it(timeout=ONE_SECOND)
                updated_row_count = db.update_balance(
                    account_id,
                    before.balance - withdrawal)

                tprint(f'updated {updated_row_count} rows')

                after = db.select_by_id(account_id)
                tprint(f'after: {after}')

                db.commit_transaction()
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_LOCK_DEADLOCK:
                    tprint('(expected) deadlock encountered')
                else:
                    raise err

    return withdraw_closure

if __name__ == '__main__':
    unittest.main()
