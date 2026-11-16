"""Transactions: real movements on Geldorte and transfers between Töpfe."""

from datetime import date
from enum import Enum

from finance_manager.model.config import UserConfig
from finance_manager.model.errors import (
    SameTopfTransferError,
    SplitGeldortMismatchError,
    SplitSourceMismatchError,
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

    A RealTransaction belongs to exactly one Topf, or to none yet, e.g.
    right after import. If it has to be split, it is assigned to one Topf
    and the parts are moved on with TopfTransfers.
    """

    def __init__(
        self,
        config: UserConfig,
        value: Value,
        transaction_date: date,
        geldort: Geldort,
        statement_text: str = "",
        mark: TransactionMark | None = None,
        topf: Topf | None = None,
    ) -> None:
        super().__init__(value, transaction_date)
        number = config.count_up_transaction(transaction_date)
        self._identifier = (
            f"{transaction_date.year}_{transaction_date.month:02d}_{number:04d}"
        )
        self._geldort = geldort
        self._statement_text = statement_text
        self._mark = mark
        self._topf = topf

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

    @property
    def topf(self) -> Topf | None:
        """The Topf this transaction belongs to, or None if not assigned yet."""
        return self._topf

    def get_mark(self) -> TransactionMark | None:
        """Return the mark of this transaction, or None if it is not marked."""
        return self._mark

    def assign_topf(self, topf: Topf) -> None:
        """Assign this transaction to a Topf, replacing any earlier assignment."""
        self._topf = topf


class TopfTransfer(Transaction):
    """An internal transfer from one Topf to another. No real money moves.

    Every TopfTransfer gets a unique identifier from the year and month of
    its date, the name of the source Topf and a number that counts up per
    month and source Topf, e.g. "2026_03_Urlaub_0002".
    The Value is always positive; source and target give the direction.
    The money stays at the same Geldort; only its Topf changes there.

    split_of links the transfer to the RealTransaction it splits, e.g. the part
    of a shopping trip that belongs to another Topf. Such a part counts as an
    expense of the target Topf. A split must start from the Topf and Geldort
    of that RealTransaction. Without split_of, the transfer only moves saved
    money between Töpfe.
    """

    def __init__(
        self,
        config: UserConfig,
        value: Value,
        transaction_date: date,
        source: Topf,
        target: Topf,
        geldort: Geldort,
        split_of: RealTransaction | None = None,
    ) -> None:
        if value.number <= 0:
            raise TransactionValueNotPositiveError(value.number)
        if source is target:
            raise SameTopfTransferError(source.name)
        if split_of is not None:
            check_split_fits_transaction(source, geldort, split_of)
        super().__init__(value, transaction_date)
        number = config.count_up_topf_transfer(transaction_date, source.name)
        self._identifier = (
            f"{transaction_date.year}_{transaction_date.month:02d}_"
            f"{source.name}_{number:04d}"
        )
        self._source = source
        self._target = target
        self._geldort = geldort
        self._split_of = split_of

    @property
    def identifier(self) -> str:
        """The unique identifier, e.g. "2026_03_Urlaub_0002"."""
        return self._identifier

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

    @property
    def split_of(self) -> RealTransaction | None:
        """The RealTransaction this transfer splits, or None for a plain transfer."""
        return self._split_of


def check_split_fits_transaction(
    source: Topf, geldort: Geldort, split_of: RealTransaction
) -> None:
    """Raise an error if a split does not start where the RealTransaction is."""
    if split_of.topf is not source:
        raise SplitSourceMismatchError(split_of.identifier, source.name)
    if split_of.geldort is not geldort:
        raise SplitGeldortMismatchError(split_of.identifier, geldort.identifier)


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
