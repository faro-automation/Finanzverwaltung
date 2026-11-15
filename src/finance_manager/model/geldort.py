"""Geldorte: the places where money actually is."""

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum

from finance_manager.model.config import UserConfig
from finance_manager.model.errors import (
    GeldortAlreadyClosedError,
    GeldortValueNotZeroError,
)
from finance_manager.model.money import Value


class GeldortStatus(Enum):
    """Whether a Geldort is still in use."""

    ACTIVE = "active"
    CLOSED = "closed"


class Kontoart(Enum):
    """The kind of a Bankkonto, named like the products German banks offer."""

    GIROKONTO = "Girokonto"
    TAGESGELDKONTO = "Tagesgeldkonto"
    FESTGELDKONTO = "Festgeldkonto"
    SPARBUCH = "Sparbuch"
    SPARBRIEF = "Sparbrief"
    BAUSPARVERTRAG = "Bausparvertrag"
    KREDITKARTENKONTO = "Kreditkartenkonto"


class Geldort(ABC):
    """A place where money actually is.

    Every Geldort gets a unique identifier from two parts and a number that
    counts up per combination of these parts, e.g. "ING_Tagesgeldkonto_02".
    The counting happens in the UserConfig, so every user counts separately.
    A new Geldort starts with an actual value of zero; for the first setup
    it can be set with set_actual_value().
    A Geldort is never deleted, only closed, so its identifier is never reused.
    """

    def __init__(self, config: UserConfig, name: str) -> None:
        self._name = name
        parts = self.get_identifier_parts()
        number = config.count_up_geldort(parts)
        self._identifier = f"{parts[0]}_{parts[1]}_{number:02d}"
        self._actual_value = Value(Decimal(0))
        self._status = GeldortStatus.ACTIVE

    @property
    def name(self) -> str:
        """The name chosen by the user."""
        return self._name

    @property
    def identifier(self) -> str:
        """The unique identifier, e.g. "ING_Tagesgeldkonto_02"."""
        return self._identifier

    @property
    def status(self) -> GeldortStatus:
        """Whether the Geldort is active or closed."""
        return self._status

    @property
    def is_active(self) -> bool:
        """Whether the Geldort is still in use."""
        return self._status is GeldortStatus.ACTIVE

    @abstractmethod
    def get_identifier_parts(self) -> tuple[str, str]:
        """Return the two parts the identifier is built from."""

    def get_actual_value(self) -> Value:
        """Return how much money is currently at this Geldort."""
        return self._actual_value

    def set_actual_value(self, value: Value) -> None:
        """Set how much money is currently there, e.g. at the first setup."""
        self._actual_value = value

    def close(self) -> None:
        """Mark the Geldort as closed. It and its identifier are kept.

        Only possible when the actual value is zero.
        """
        if not self.is_active:
            raise GeldortAlreadyClosedError(self._identifier)
        if self._actual_value.number != 0:
            raise GeldortValueNotZeroError(self._identifier, self._actual_value.number)
        self._status = GeldortStatus.CLOSED


class Bankkonto(Geldort):
    """A bank account, identified like "ING_Tagesgeldkonto_01"."""

    def __init__(
        self, config: UserConfig, name: str, bank: str, kontoart: Kontoart
    ) -> None:
        # Set before the base class builds the identifier from them.
        self._bank = bank
        self._kontoart = kontoart
        super().__init__(config, name)

    @property
    def bank(self) -> str:
        """The bank that holds the account."""
        return self._bank

    @property
    def kontoart(self) -> Kontoart:
        """The kind of account."""
        return self._kontoart

    def get_identifier_parts(self) -> tuple[str, str]:
        """Return bank and Kontoart."""
        return (self._bank, self._kontoart.value)


class Bargeld(Geldort):
    """Cash, e.g. the Schublade, identified like "Bargeld_Schublade_01"."""

    def get_identifier_parts(self) -> tuple[str, str]:
        """Return "Bargeld" and the chosen name."""
        return ("Bargeld", self._name)


class Gutscheine(Geldort):
    """A collection of vouchers counting as money, e.g. "Gutscheine_Geburtstag_01"."""

    def get_identifier_parts(self) -> tuple[str, str]:
        """Return "Gutscheine" and the chosen name."""
        return ("Gutscheine", self._name)
