from abc import ABC, abstractmethod
from datetime import datetime, timezone


class USD:
    '''quantity of money in units of United States Dollars (USD)'''

    _total_cents: int
    _dollars: int
    _cents: int
    _sign: int # always -1 or +1

    _CENTS_PER_DOLLAR = 100

    ## keep our quantities within a 32-bit signed int
    MAX_CENTS = 2**31 - 1
    MIN_CENTS = -2**31

    def __init__(self, cents: int):
        '''
        :raises OutOfRange when the supplied value falls outside the range
        [USD.MIN_CENTS, USD.MAX_CENTS]
        '''
        if cents < USD.MIN_CENTS or USD.MAX_CENTS < cents:
            raise ValueError(
                f'the supplied value {cents} was outside the allowed '
                f'range [{USD.MIN_CENTS}, {USD.MAX_CENTS}]')

        self._total_cents = cents

        (d, c) = divmod(
            abs(self._total_cents),
            USD._CENTS_PER_DOLLAR)
        self._sign = -1 if cents < 0 else 1
        self._dollars = self._sign * d
        self._cents = self._sign * c

    @property
    def total_cents(self):
        '''ONLY FOR USE IN SERIALIZATION, DESERIALIZATION!'''
        return self._total_cents

    def __str__(self):
        sign = '-' if self._sign < 0 else ''
        return f'${sign}{abs(self._dollars):0,}.{abs(self._cents):02d}'

    def __repr__(self):
        return f'USD({self._total_cents})'

    def __eq__(self, other):
        if isinstance(other, USD):
            return self._total_cents == other._total_cents

        raise NotImplementedError(f'cannot compare USD to {type(other)}')

USD.ZERO = USD(0)

class Account:
    '''a single bank account'''
    _id: int
    _full_name: str
    _balance: USD
    _closed_at: datetime | None

    def __init__(
            self,
            acct_id: int,
            full_name: str,
            balance: USD,
            closed_at: datetime | None):
        self._id = acct_id
        self._full_name = full_name
        self._balance = balance

        if closed_at is None:
            self._closed_at = None
        elif closed_at.tzinfo is None:
            raise ValueError('closed_at.tzinfo may not be None')
        else:
            self._closed_at = closed_at

    @property
    def id(self):
        '''account number/ID'''
        return self._id

    def __str__(self):
        return 'Account(' \
            f'acct_id={self._id}, ' \
            f'full_name={q(self._full_name)}", ' \
            f'balance_usd_cents={self._balance}, ' \
            f'closed_at_utc={q(self._closed_at)}' \
            ')'

def q(x) -> str:
    '''quoted string-ified version of `x`, or "None"'''
    return 'None' if x is None else f'"{str(x)}"'

class BankDatabase(ABC):
    @abstractmethod
    def select_by_id(self, account_id: int) -> Account:
        pass
    @abstractmethod
    def insert(self, full_name: str, balance: USD, closed_at: datetime) -> Account:
        pass
    @abstractmethod
    def update_closed_at(self, account_id: int, closed_at: datetime) -> Account:
        pass
    @abstractmethod
    def update_name(self, account_id: int, full_name: str) -> None:
        pass
    @abstractmethod
    def update_balance(self, account_id: int, balance: USD) -> None:
        pass
    @abstractmethod
    def begin_serializable_transaction(self) -> None:
        pass
    @abstractmethod
    def commit_transaction(self) -> None:
        pass

class Bank:
    def __init__(self, database: BankDatabase):
        self._db = database

    def open_account(self, full_name: str) -> Account:
        ## BUG: Don't allow empty/whitespace names.
        return self._db.insert(full_name, USD.ZERO, None)

    def load(self, account_id: int) -> Account:
        return self._db.select_by_id(account_id)

    def close_account(self, account_id: int) -> Account:
        ## BUG: forbid closing an account with a non-zero balance
        self._db.update_closed_at(account_id, datetime.now(timezone.utc))
        return self.load(account_id)

    def alter_name(self, account_id: int, full_name: str) -> Account:
        ## BUG: forbid changes to closed accounts
        self._db.update_name(account_id, full_name)
        return self.load(account_id)

    def deposit(self, account_id: int, amount: USD) -> Account:
        ## BUG: forbid deposits to closed accounts
        ## BUG: need a database transaction
        account = self.load(account_id)
        self._db.update_balance(account_id, account.balance + amount)
        return self.load(account_id)

    def withdraw(self, account_id: int, amount: USD) -> Account:
        ## BUG: forbid overdraft (i.e., can't have negative balance)
        ## BUG: need a database transaction
        account = self.load(account_id)
        self._db.update_balance(account_id, account.balance - amount)
        return self.load(account_id)
