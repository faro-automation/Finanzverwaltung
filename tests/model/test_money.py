from decimal import Decimal

import pytest

from finance_manager.model import Currency, Value
from finance_manager.model.errors import InvalidValueError


def test_euro_has_symbol_and_decimal_places() -> None:
    assert Currency.EURO.symbol == "€"
    assert Currency.EURO.decimal_places == 2


def test_exchange_rate_is_not_set_yet() -> None:
    assert Currency.EURO.exchange_rate is None


def test_smallest_unit_follows_decimal_places() -> None:
    assert Currency.EURO.smallest_unit == Decimal("0.01")


def test_value_is_in_euro_by_default() -> None:
    assert Value(Decimal("12.50")).currency == Currency.EURO


def test_is_negative_follows_sign_of_number() -> None:
    assert Value(Decimal("-12.50")).is_negative
    assert not Value(Decimal("12.50")).is_negative
    assert not Value(Decimal("0")).is_negative


def test_value_rejects_more_decimals_than_currency_allows() -> None:
    with pytest.raises(InvalidValueError):
        Value(Decimal("1.005"))


def test_equal_values_are_equal() -> None:
    assert Value(Decimal("5.00")) == Value(Decimal("5"))
