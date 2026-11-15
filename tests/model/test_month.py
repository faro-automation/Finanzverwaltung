import pytest

from finance_manager.model import Month
from finance_manager.model.errors import InvalidMonthError


def test_month_keeps_year_and_number() -> None:
    januar = Month(2027, 1)

    assert januar.year == 2027
    assert januar.number == 1


@pytest.mark.parametrize("number", [0, 13])
def test_month_rejects_number_outside_calendar(number: int) -> None:
    with pytest.raises(InvalidMonthError):
        Month(2027, number)
