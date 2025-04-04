from datetime import datetime, timezone
import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection

from domain import USD, Account, BankDatabase


class BankMySqlDatabase(BankDatabase):
    '''the Bank's MySQL database of accounts'''
    connection: PooledMySQLConnection

    def __init__(self):
        self.connection = None

    def __enter__(self):
        '''open the connection'''
        self.connection = mysql.connector.connect(
            database = 'elite102',
            user = 'elite102',
            password = 'password',
            pool_name = 'BankDatabase')
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        '''close the connection'''
        if self.connection:
            self.connection.close()

    def select_by_id(self, account_id: int) -> Account:
        '''
        Select a single account row by ID; returns None if the ID does not exist
        in the accounts table
        '''
        cursor = self.connection.cursor()
        cursor.execute('''
            select
                    id,
                    full_name,
                    balance_usd_cents,
                    closed_at_utc
                from
                    account
                where
                    id = %(id)s
            ''',
            {
                'id': account_id,
            })
        row = next(cursor, None)
        if row is None:
            return None

        (acct_id, name, balance, closed_at) = row
        if closed_at is not None:
            closed_at = closed_at.replace(tzinfo=timezone.utc)

        return Account(acct_id, name, balance, closed_at)

    def insert(
            self,
            full_name: str,
            balance: USD,
            closed_at: datetime,
            ) -> Account:
        '''
        insert a row for the never-before-saved Account
        '''
        # closed_at_utc = closed_at.astimezone(timezone.utc)
        cursor = self.connection.cursor()
        cursor.execute(
            '''
            insert into account (
                    full_name,     balance_usd_cents,     closed_at_utc
                ) values (
                    %(full_name)s, %(balance_usd_cents)s, %(closed_at_utc)s
                );
            ''',
            {
                'full_name': full_name,
                'balance_usd_cents': balance,
                'closed_at_utc': closed_at,
            })
        self.connection.commit()
        account_id = cursor.lastrowid
        return Account(account_id, full_name, balance, closed_at)

    def update_closed_at(self, account_id: int, closed_at: datetime) -> None:
        '''record the date-time at which an account is closed'''
        cursor = self.connection.cursor()
        cursor.execute('''
            update account set
                    closed_at_utc = %(closed_at_utc)s
                where
                    id = %(id)s
                ;
            ''',
            {
                'closed_at_utc': closed_at,
                'id': account_id,
            })

    def update_name(self, account_id: int, full_name: str) -> None:
        '''alter the name of the account owner'''
        cursor = self.connection.cursor()
        cursor.execute('''
            update account set
                    full_name = %(full_name)s
                where
                    id = %(id)s
                ;
            ''',
            {
                'full_name': full_name,
                'id': account_id,
            })

    def update_balance(self, account_id: int, balance: USD) -> None:
        '''
        Select a single account row by ID; returns None if the ID does not exist
        in the accounts table
        '''
        cursor = self.connection.cursor()
        cursor.execute('''
            update account set
                    balance_usd_cents = %(balance_usd_cents)s
                where
                    id = %(id)s
                ;
            ''',
            {
                'balance_usd_cents': balance.total_cents,
                'id': account_id,
            })

    def begin_serializable_transaction(self):
        self.connection.start_transaction(isolation_level='SERIALIZABLE')

    def commit_transaction(self):
        self.connection.commit()

def select_and_print(db, acct_id):
    account = db.select_by_id(acct_id)
    print(f'selected {account}')

def main():
    with BankMySqlDatabase() as db:
        account = db.insert('Frank the Cat', 0, None)
        print(f'inserted {account}')
        select_and_print(db, account.id)

        db.update_name(account.id, 'Frank the Awesome Cat')
        select_and_print(db, account.id)

        db.update_balance(account.id, USD(123_45))
        select_and_print(db, account.id)

        db.update_closed_at(account.id, datetime.now(timezone.utc))
        select_and_print(db, account.id)

if __name__ == '__main__':
    main()
