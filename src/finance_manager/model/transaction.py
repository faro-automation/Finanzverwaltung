"""Transactions: real movements on Geldorte and transfers between Töpfe."""

from datetime import date
from enum import Enum

from finance_manager.model.config import UserConfig
from finance_manager.model.errors import (
    SameTopfTransferError,
    TransactionValueNotPositiveError,
)
from finance_manager.model.geldort import Geldort
from finance_manager.model.money import Value
from finance_manager.model.topf import Topf


class Direction(Enum):
    """Whether money comes into or goes out of a Geldort."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"


class TransactionMark(Enum):
    """A mark on a RealTransaction for money paid for someone else.

    German names: the English terms (advance, reimbursement) are ambiguous.
    """

    AUSLAGE = "auslage"
    RUECKZAHLUNG = "rueckzahlung"


class Transaction:
    """Any movement of money on a given day. Unchangeable once created."""

    def __init__(self, value: Value, transaction_date: date) -> None:
        self._value = value
        self._transaction_date = transaction_date

    @property
    def value(self) -> Value:
        """How much money moves."""
        return self._value

    @property
    def transaction_date(self) -> date:
        """The day of the movement."""
        return self._transaction_date


class RealTransaction(Transaction):
    """A real movement of money on a Geldort, e.g. one line of a bank statement.

    Every RealTransaction gets a unique identifier from the year and month of
    its date and a number that counts up per month, e.g. "2026_03_0042".
    The counting happens in the UserConfig, so every user counts separately.
    The sign of the Value gives the Direction: positive is incoming,
    negative is outgoing. The statement_text is the text from the bank
    statement. The mark flags an Auslage or a Rueckzahlung.
    """

    def __init__(
        self,
        config: UserConfig,
        value: Value,
        transaction_date: date,
        geldort: Geldort,
        statement_text: str = "",
        mark: TransactionMark | None = None,
    ) -> None:
        super().__init__(value, transaction_date)
        number = config.count_up_transaction(transaction_date)
        self._identifier = (
            f"{transaction_date.year}_{transaction_date.month:02d}_{number:04d}"
        )
        self._geldort = geldort
        self._statement_text = statement_text
        self._mark = mark

    @property
    def identifier(self) -> str:
        """The unique identifier, e.g. "2026_03_0042"."""
        return self._identifier

    @property
    def geldort(self) -> Geldort:
        """Where the money moves."""
        return self._geldort

    @property
    def statement_text(self) -> str:
        """The text from the bank statement."""
        return self._statement_text

    @property
    def direction(self) -> Direction:
        """Incoming or outgoing, matching the sign of the Value."""
        return Direction.OUTGOING if self._value.is_negative else Direction.INCOMING

    def get_mark(self) -> TransactionMark | None:
        """Return the mark of this transaction, or None if it is not marked."""
        return self._mark


class TopfTransfer(Transaction):
    """An internal transfer from one Topf to another. No real money moves.

    The Value is always positive; source and target give the direction.
    The money stays at the same Geldort; only its Topf changes there.
    """

    def __init__(
        self,
        value: Value,
        transaction_date: date,
        source: Topf,
        target: Topf,
        geldort: Geldort,
    ) -> None:
        if value.number <= 0:
            raise TransactionValueNotPositiveError(value.number)
        if source is target:
            raise SameTopfTransferError(source.name)
        super().__init__(value, transaction_date)
        self._source = source
        self._target = target
        self._geldort = geldort

    @property
    def source(self) -> Topf:
        """The Topf the money comes from."""
        return self._source

    @property
    def target(self) -> Topf:
        """The Topf the money goes to."""
        return self._target

    @property
    def geldort(self) -> Geldort:
        """The Geldort where the money stays."""
        return self._geldort


class Auslage:
    """Money paid for someone else that is expected back.

    The transaction is the outgoing payment. Each Rueckzahlung is an incoming
    RealTransaction. Their values are not compared with the Auslage: people
    often pay back only their part, or a rounded amount.
    Instead, the Auslage knows how many Rueckzahlungen are expected,
    e.g. two when two people owe their part. By default one is expected.
    """

    def __init__(
        self, transaction: RealTransaction, expected_rueckzahlung_amount: int = 1
    ) -> None:
        self._transaction = transaction
        self._expected_rueckzahlung_amount = expected_rueckzahlung_amount
        self._rueckzahlungen: list[RealTransaction] = []

    @property
    def transaction(self) -> RealTransaction:
        """The outgoing payment."""
        return self._transaction

    @property
    def expected_rueckzahlung_amount(self) -> int:
        """How many Rueckzahlungen are expected."""
        return self._expected_rueckzahlung_amount

    @property
    def rueckzahlungen(self) -> tuple[RealTransaction, ...]:
        """All Rueckzahlungen assigned so far; add more with add_rueckzahlung."""
        return tuple(self._rueckzahlungen)

    @property
    def has_rueckzahlung(self) -> bool:
        """Whether at least one Rueckzahlung has been assigned."""
        return len(self._rueckzahlungen) > 0

    @property
    def is_open(self) -> bool:
        """Whether fewer Rueckzahlungen arrived than expected."""
        return len(self._rueckzahlungen) < self._expected_rueckzahlung_amount

    def add_rueckzahlung(self, rueckzahlung: RealTransaction) -> None:
        """Assign a Rueckzahlung to this Auslage."""
        self._rueckzahlungen.append(rueckzahlung)

    def change_expected_rueckzahlung_amount(self, amount: int) -> None:
        """Set how many Rueckzahlungen are expected."""
        self._expected_rueckzahlung_amount = amount
