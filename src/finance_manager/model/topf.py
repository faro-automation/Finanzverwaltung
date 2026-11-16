"""Topf: the virtual assignment of money to a purpose."""

from decimal import Decimal
from enum import Enum

from finance_manager.model.config import UserConfig
from finance_manager.model.errors import (
    TopfAlreadyAufgeloestError,
    TopfRenameNotAfterLastRenameError,
    TopfValueNotZeroError,
)
from finance_manager.model.geldort import Geldort
from finance_manager.model.money import Value
from finance_manager.model.month import Month


class TopfStatus(Enum):
    """Whether a Topf is still in use."""

    ACTIVE = "active"
    AUFGELOEST = "aufgeloest"


class Topf:
    """A purpose that money is assigned to, independent of where it actually is.

    The name identifies the Topf: it is chosen by the user and unique per user.
    A Topf can be renamed from a given month on; the names used before stay
    known for the months they applied to and stay reserved, so no other Topf
    can take them.
    The main_geldort is where the Topf's money should ideally be.
    The geldort_values say how much of the Topf's money is at which Geldort,
    keyed by the Geldort's identifier. A Geldort whose value reaches zero is
    removed. The actual value of the Topf is always the sum of these values;
    it may be negative.
    """

    def __init__(
        self,
        config: UserConfig,
        name: str,
        main_geldort: Geldort,
        geldort_values: dict[str, Value] | None = None,
    ) -> None:
        config.register_topf_name(name)
        self._first_name = name
        self._renames: list[tuple[Month, str]] = []
        self._main_geldort = main_geldort
        self._geldort_values = {
            identifier: value
            for identifier, value in (geldort_values or {}).items()
            if value.number != 0
        }
        self._status = TopfStatus.ACTIVE

    @property
    def name(self) -> str:
        """The current name: the one from the latest rename, or the first name."""
        return self._renames[-1][1] if self._renames else self._first_name

    @property
    def main_geldort(self) -> Geldort:
        """Where the Topf's money should ideally be."""
        return self._main_geldort

    @property
    def geldort_values(self) -> dict[str, Value]:
        """A copy of how much is at which Geldort; change it with add_geldort_value."""
        return dict(self._geldort_values)

    @property
    def status(self) -> TopfStatus:
        """Whether the Topf is active or aufgelöst."""
        return self._status

    @property
    def is_active(self) -> bool:
        """Whether the Topf can still receive money."""
        return self._status is TopfStatus.ACTIVE

    def get_name(self, month: Month) -> str:
        """Return the name that applied in the given month."""
        name = self._first_name
        for valid_from, new_name in self._renames:
            if valid_from <= month:
                name = new_name
        return name

    def rename(self, config: UserConfig, new_name: str, valid_from: Month) -> None:
        """Rename the Topf from the given month on.

        The new name must not be taken yet, and the month must come after the
        month of the latest rename.
        """
        if self._renames and valid_from <= self._renames[-1][0]:
            last_month = self._renames[-1][0]
            raise TopfRenameNotAfterLastRenameError(
                self.name, f"{last_month.year}-{last_month.number:02d}"
            )
        config.register_topf_name(new_name)
        self._renames.append((valid_from, new_name))

    def add_geldort_value(self, geldort: Geldort, value: Value) -> None:
        """Add a value at a Geldort.

        The value is added to what is already there. If the result is zero,
        the Geldort is removed from the Topf.
        """
        identifier = geldort.identifier
        current = self._geldort_values.get(identifier, Value(Decimal(0)))
        new_number = current.number + value.number
        if new_number == 0:
            self._geldort_values.pop(identifier, None)
        else:
            self._geldort_values[identifier] = Value(new_number)

    def get_actual_value(self) -> Value:
        """Return how much money the Topf currently holds: the sum of its values."""
        total = sum(
            (value.number for value in self._geldort_values.values()), Decimal(0)
        )
        return Value(total)

    def aufloesen(self) -> None:
        """Mark the Topf as aufgelöst. Its history is kept.

        Only possible when the actual value is zero; any remaining money must
        first be moved to another Topf with a TopfTransfer.
        """
        if not self.is_active:
            raise TopfAlreadyAufgeloestError(self.name)
        actual_number = self.get_actual_value().number
        if actual_number != 0:
            raise TopfValueNotZeroError(self.name, actual_number)
        self._status = TopfStatus.AUFGELOEST
