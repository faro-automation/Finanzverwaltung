"""Salary plans: the planned salary and how it is split into Töpfe."""

from dataclasses import dataclass, replace
from decimal import Decimal

from finance_manager.model.errors import (
    SalaryAllocationExceedsSalaryError,
    SalaryPartItemNotFoundError,
    SalaryPartNotFoundError,
)
from finance_manager.model.geldort import Geldort
from finance_manager.model.money import Value
from finance_manager.model.month import Month
from finance_manager.model.topf import Topf


@dataclass(frozen=True)
class SalaryPartItem:
    """One named item of a SalaryPart, e.g. "Haftpflicht" with 10 €."""

    name: str
    value: Value


@dataclass(frozen=True)
class SalaryPart:
    """The part of the salary that goes into one Topf at one Geldort.

    The part consists of named items, e.g. one per insurance; its value is
    always the sum of these items.
    If the geldort differs from where the salary arrives, the money has to be
    moved there, usually by a standing order for this Topf.
    Parts are unchangeable; SalaryPlan replaces them, so every change is
    checked against the salary.
    """

    topf: Topf
    geldort: Geldort
    items: tuple[SalaryPartItem, ...] = ()

    def get_value(self) -> Value:
        """Return the value of this part: the sum of its items."""
        total = sum((item.value.number for item in self.items), Decimal(0))
        return Value(total)


@dataclass(frozen=True)
class Salary:
    """The planned monthly salary: how much, where it arrives, which Topf holds it.

    The geldort is where the salary arrives as one booking.
    The topf is a real Topf that holds the salary from its arrival (often
    already in the month before) until it is split by the SalaryPlan.
    """

    value: Value
    geldort: Geldort
    topf: Topf


class SalaryPlan:
    """The planned monthly salary and its allocation to Töpfe.

    The salary is split into the Töpfe of the allocation; whatever is left
    goes to the remainder_topf (Resttopf).
    A plan is valid from its valid_from month on. When the salary or the
    allocation changes, a new plan with a later valid_from is added; older
    plans are kept, so it stays traceable what applied when.

    The allocated parts must never add up to more than the salary. Salary and
    allocation can only be changed through the methods below; every change is
    checked first and rejected with an error if it breaks the rule, so the
    plan always stays valid.
    """

    def __init__(
        self,
        salary: Salary,
        remainder_topf: Topf,
        valid_from: Month,
        allocation: tuple[SalaryPart, ...] = (),
    ) -> None:
        check_allocation_fits_salary(salary.value, allocation)
        self._salary = salary
        self._remainder_topf = remainder_topf
        self._valid_from = valid_from
        self._allocation = allocation

    @property
    def salary(self) -> Salary:
        """The planned monthly salary with its Geldort and Topf."""
        return self._salary

    @property
    def remainder_topf(self) -> Topf:
        """The Topf that gets whatever is left (Resttopf)."""
        return self._remainder_topf

    @property
    def valid_from(self) -> Month:
        """The month from which this plan applies."""
        return self._valid_from

    @property
    def allocation(self) -> tuple[SalaryPart, ...]:
        """All parts of the allocation."""
        return self._allocation

    def get_allocated_value(self) -> Value:
        """Return the sum of all parts of the allocation."""
        return sum_parts(self._allocation)

    def get_remainder_value(self) -> Value:
        """Return what is left of the salary for the remainder_topf."""
        return Value(self._salary.value.number - self.get_allocated_value().number)

    def change_salary_value(self, value: Value) -> None:
        """Set a new value for the salary."""
        self._commit(replace(self._salary, value=value), self._allocation)

    def add_part(self, part: SalaryPart) -> None:
        """Add a part for a Topf to the allocation."""
        self._commit(self._salary, (*self._allocation, part))

    def remove_part(self, topf: Topf) -> None:
        """Remove the part of a Topf from the allocation."""
        index = self._find_part_index(topf)
        allocation = self._allocation[:index] + self._allocation[index + 1 :]
        self._commit(self._salary, allocation)

    def add_item(self, topf: Topf, item: SalaryPartItem) -> None:
        """Add an item to the part of a Topf."""
        index = self._find_part_index(topf)
        part = self._allocation[index]
        self._replace_part(index, replace(part, items=(*part.items, item)))

    def remove_item(self, topf: Topf, item_name: str) -> None:
        """Remove an item, found by its name, from the part of a Topf."""
        index = self._find_part_index(topf)
        part = self._allocation[index]
        item_index = find_item_index(part, item_name)
        items = part.items[:item_index] + part.items[item_index + 1 :]
        self._replace_part(index, replace(part, items=items))

    def change_item_value(self, topf: Topf, item_name: str, value: Value) -> None:
        """Change the value of an item, found by its name, in the part of a Topf."""
        index = self._find_part_index(topf)
        part = self._allocation[index]
        item_index = find_item_index(part, item_name)
        items = (
            *part.items[:item_index],
            SalaryPartItem(item_name, value),
            *part.items[item_index + 1 :],
        )
        self._replace_part(index, replace(part, items=items))

    def _replace_part(self, index: int, part: SalaryPart) -> None:
        """Put a changed part in place of the part at this position."""
        allocation = (
            *self._allocation[:index],
            part,
            *self._allocation[index + 1 :],
        )
        self._commit(self._salary, allocation)

    def _commit(self, salary: Salary, allocation: tuple[SalaryPart, ...]) -> None:
        """Take over salary and allocation, but only if they fit together."""
        check_allocation_fits_salary(salary.value, allocation)
        self._salary = salary
        self._allocation = allocation

    def _find_part_index(self, topf: Topf) -> int:
        """Return the position of the part that belongs to this Topf."""
        index = next(
            (
                position
                for position, part in enumerate(self._allocation)
                if part.topf is topf
            ),
            None,
        )
        if index is None:
            raise SalaryPartNotFoundError(topf.name)
        return index


def sum_parts(parts: tuple[SalaryPart, ...]) -> Value:
    """Return the sum of the values of these parts."""
    total = sum((part.get_value().number for part in parts), Decimal(0))
    return Value(total)


def check_allocation_fits_salary(
    salary: Value, allocation: tuple[SalaryPart, ...]
) -> None:
    """Raise an error if the allocation adds up to more than the salary."""
    allocated = sum_parts(allocation)
    if allocated.number > salary.number:
        raise SalaryAllocationExceedsSalaryError(salary.number, allocated.number)


def find_item_index(part: SalaryPart, item_name: str) -> int:
    """Return the position of the item with this name in the part."""
    index = next(
        (
            position
            for position, item in enumerate(part.items)
            if item.name == item_name
        ),
        None,
    )
    if index is None:
        raise SalaryPartItemNotFoundError(part.topf.name, item_name)
    return index
