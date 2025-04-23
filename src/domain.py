from abc import ABC, abstractmethod
from datetime import datetime
import re


AccountId = int

class USD:
    '''quantity of money in units of United States Dollars (USD)'''

    _total_cents: int
    _dollars: int
    _cents: int
    _sign: int # always -1 or +1

    _CENTS_PER_DOLLAR = 100
    ##                      spaces $  dollars   . cents spaces
    _PATTERN = re.compile(r'^ \s* \$? ([\d,]+) \. (\d\d) \s* $', re.VERBOSE)

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

    @staticmethod
    def parse(amount_str: str) -> 'USD':
        match = USD._PATTERN.match(amount_str)

        if match is None:
            raise ValueError(f'unrecognized USD quantity: {amount_str}')

        dollars = int(match.group(1).replace(',', ''))
        franctional_cents = int(match.group(2))

        total_cents = (100 * dollars) + franctional_cents
        return USD(total_cents)

USD.ZERO = USD(0)

def validated_full_name(full_name: str) -> str:
    '''
    returns the supplied full name, or raises ValueError when it is invalid
    '''
    if full_name is None or len(full_name.strip()) == 0:
        raise ValueError('full_name must contain non-whitespace characters')

    return full_name

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
        self._full_name = validated_full_name(full_name)
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

    @property
    def is_open(self) -> bool:
        return self._closed_at is None

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
    @abstractmethod
    def rollback_transaction(self) -> None:
        raise NotImplementedError()

class Clock(ABC):
    @abstractmethod
    def utcnow(self) -> datetime:
        '''the current time '''
        raise NotImplementedError()

class BoolLike(ABC):
    @abstractmethod
    def __bool__(self):
        raise NotImplementedError()

class Bank:
    def __init__(self, database: BankDatabase, clock: Clock):
        self._db = database
        self._clock = clock

    def open_account(self, full_name: str) -> Account:
        self._db.start_serializable_transaction()
        try:
            account = self._db.insert(Account.new(full_name))
            self._db.commit_transaction()
            return account
        except:
            self._db.rollback_transaction()
            raise

    def _load(self, account_id: AccountId) -> Account:
        return self._db.select_by_id(account_id)

    def load(self, account_id: AccountId) -> Account:
        self._db.start_serializable_transaction()
        try:
            result = self._db.select_by_id(account_id)
            self._db.commit_transaction()
            return result
        except:
            self._db.rollback_transaction()
            raise

    def close_account(self, account_id: AccountId) -> Account:
        self._db.start_serializable_transaction()
        try:
            before = self._load(account_id)

            if not before.is_open:
                return before

            if before.balance != USD.ZERO:
                raise ValueError('cannot close account with non-zero balance')

            self._db.update_closed_at(account_id, self._clock.utcnow())
            after = self._load(account_id)
            self._db.commit_transaction()
            return after
        except:
            self._db.rollback_transaction()
            raise

    def alter_name(self, account_id: AccountId, full_name: str) -> Account:
        full_name = validated_full_name(full_name)
        self._db.start_serializable_transaction()
        try:
            account = self._load(account_id)

            if not account.is_open:
                raise ValueError('cannot alter closed account')

            self._db.update_name(account_id, full_name)
            after = self._load(account_id)
            self._db.commit_transaction()
            return after
        except:
            self._db.rollback_transaction()
            raise

    def deposit(self, account_id: AccountId, amount: USD) -> Account:
        self._db.start_serializable_transaction()
        try:
            account = self._load(account_id)
            if not account.is_open:
                raise ValueError('cannot deposit into closed account')

            self._db.update_balance(account_id, account.balance + amount)
            after = self._load(account_id)
            self._db.commit_transaction()
            return after
        except:
            self._db.rollback_transaction()
            raise

    def withdraw(self, account_id: AccountId, amount: USD) -> Account:
        self._db.start_serializable_transaction()
        try:
            account = self._load(account_id)
            if not account.is_open:
                raise ValueError('cannot withdraw from closed account')

            if account.balance < amount:
                raise ValueError('cannot withdraw more than current balance')

            self._db.update_balance(account_id, account.balance - amount)
            after = self._load(account_id)
            self._db.commit_transaction()
            return after
        except:
            self._db.rollback_transaction()
            raise
