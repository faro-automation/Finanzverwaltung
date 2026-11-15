"""Month: a calendar month with its year."""

from dataclasses import dataclass

from finance_manager.model.errors import InvalidMonthError

JANUARY = 1
DECEMBER = 12


@dataclass(frozen=True)
class Month:
    """A calendar month, e.g. Month(2027, 1) for January 2027."""

    year: int
    number: int

    def __post_init__(self) -> None:
        if not JANUARY <= self.number <= DECEMBER:
            raise InvalidMonthError(self.number)
