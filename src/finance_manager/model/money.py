"""Money: currencies and values."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from finance_manager.model.errors import InvalidValueError


class Currency(Enum):
    """A currency with its symbol and number of decimal places.

    The exchange_rate is only a placeholder for later. It stays ``None``
    until there is a way to keep it up to date.
    """

    EURO = ("€", 2)

    def __init__(self, symbol: str, decimal_places: int) -> None:
        self.symbol = symbol
        self.decimal_places = decimal_places
        self.exchange_rate: Decimal | None = None

    @property
    def smallest_unit(self) -> Decimal:
        """The smallest amount this Currency can express, e.g. 0.01 for EURO."""
        return Decimal(10) ** -self.decimal_places


@dataclass(frozen=True)
class Value:
    """A signed amount of money in a Currency, e.g. -12.50 €.

    The number carries the sign. It is never a ``float``.
    """

    number: Decimal
    currency: Currency = Currency.EURO

    def __post_init__(self) -> None:
        if self.number != self.number.quantize(self.currency.smallest_unit):
            raise InvalidValueError(
                self.number, self.currency.symbol, self.currency.decimal_places
            )

    @property
    def is_negative(self) -> bool:
        """Whether the Value is below zero."""
        return self.number < 0
