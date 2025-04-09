from abc import ABC, abstractmethod
from datetime import datetime


AccountId = int

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

    def __add__(self, other):
        if isinstance(other, USD):
            return USD(self._total_cents + other._total_cents)

        raise NotImplementedError(f'cannot add USD to {type(other)}')

    def __sub__(self, other):
        if isinstance(other, USD):
            return USD(self._total_cents - other._total_cents)

        raise NotImplementedError(f'cannot subtract {type(other)} from USD')

    def __lt__(self, other):
        if isinstance(other, USD):
            return self._total_cents < other._total_cents

        raise NotImplementedError(f'cannot compare USD and {type(other)}')

    def __ge__(self, other):
        if isinstance(other, USD):
            return self._total_cents >= other._total_cents

        raise NotImplementedError(f'cannot compare USD and {type(other)}')

USD.ZERO = USD(0)

class Account:
    '''a single bank account'''
    _id: AccountId | None
    _full_name: str
    _balance: USD
    _closed_at: datetime | None

    @staticmethod
    def new(full_name: str) -> 'Account':
        '''create a new account'''
        return Account(None, full_name, USD.ZERO, None)

    def __init__(
            self,
            acct_id: AccountId | None,
            full_name: str,
            balance: USD,
            closed_at: datetime | None):
        '''
        "Rehydrate" an Account from data saved in some data store. Prefer
        `Account.new()` for entirely new accounts.
        '''
        self._id = acct_id

        if full_name is None or len(full_name.strip()) == 0:
            raise ValueError('full_name must contain non-whitespace characters')

        self._full_name = full_name
        self._balance = balance

        if closed_at is None:
            self._closed_at = None
        elif closed_at.tzinfo is None:
            raise ValueError('closed_at.tzinfo may not be None')
        else:
            self._closed_at = closed_at

    @property
    def id(self) -> AccountId | None:
        '''when `None`, this Account does not exist in the database'''
        return self._id

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def balance(self) -> USD:
        return self._balance

    @property
    def closed_at(self) -> datetime | None:
        return self._closed_at

    def __str__(self):
        return 'Account(' \
            f'acct_id={self._id}, ' \
            f'full_name={q(self._full_name)}", ' \
            f'balance_usd_cents={self._balance}, ' \
            f'closed_at_utc={q(self._closed_at)}' \
            ')'

    def __repr__(self):
        s = self
        return f'Account({s.id}, {q(s.full_name)}, {repr(s.balance)}, {s.closed_at})'

def q(x) -> str:
    '''quoted string-ified version of `x`, or "None"'''
    return 'None' if x is None else f'"{str(x)}"'

class BankDatabase(ABC):
    @abstractmethod
    def select_by_id(self, account_id: AccountId) -> Account:
        raise NotImplementedError()
    @abstractmethod
    def insert(self, a: Account) -> Account:
        raise NotImplementedError()
    @abstractmethod
    def update_closed_at(self, account_id: AccountId, closed_at: datetime) -> None:
        raise NotImplementedError()
    @abstractmethod
    def update_name(self, account_id: AccountId, full_name: str) -> None:
        raise NotImplementedError()
    @abstractmethod
    def update_balance(self, account_id: AccountId, balance: USD) -> None:
        raise NotImplementedError()
    @abstractmethod
    def start_serializable_transaction(self) -> None:
        raise NotImplementedError()
    @abstractmethod
    def commit_transaction(self) -> None:
        raise NotImplementedError()
