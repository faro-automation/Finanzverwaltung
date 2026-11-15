"""Domain errors raised when a rule of the financial model is violated."""

from decimal import Decimal


class FinanceError(Exception):
    """Base class for all domain errors."""


class InvalidValueError(FinanceError):
    """Raised when a Value has more decimals than its Currency allows."""

    def __init__(self, number: Decimal, symbol: str, decimal_places: int) -> None:
        super().__init__(
            f"Value {number} {symbol} must not have more than {decimal_places} decimals"
        )


class TransactionValueNotPositiveError(FinanceError):
    """Raised when a TopfTransfer's Value is zero or negative."""

    def __init__(self, number: Decimal) -> None:
        super().__init__(
            f"Transfer value {number} must be positive; "
            "source and target give the direction"
        )


class SameTopfTransferError(FinanceError):
    """Raised when a TopfTransfer has the same Topf as source and target."""

    def __init__(self, topf_name: str) -> None:
        super().__init__(f"Cannot transfer from Topf '{topf_name}' to itself")


class TopfValueNotZeroError(FinanceError):
    """Raised when dissolving a Topf that still holds money or is negative."""

    def __init__(self, topf_name: str, number: Decimal) -> None:
        super().__init__(
            f"Topf '{topf_name}' still has a value of {number}; "
            "balance it with a TopfTransfer before dissolving it"
        )


class TopfAlreadyAufgeloestError(FinanceError):
    """Raised when dissolving a Topf that is already aufgelöst."""

    def __init__(self, topf_name: str) -> None:
        super().__init__(f"Topf '{topf_name}' is already aufgelöst")


class GeldortValueNotZeroError(FinanceError):
    """Raised when closing a Geldort that still holds money or is negative."""

    def __init__(self, identifier: str, number: Decimal) -> None:
        super().__init__(
            f"Geldort '{identifier}' still has a value of {number}; "
            "it can only be closed at zero"
        )


class GeldortAlreadyClosedError(FinanceError):
    """Raised when closing a Geldort that is already closed."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Geldort '{identifier}' is already closed")


class InvalidMonthError(FinanceError):
    """Raised when a month number is outside 1 to 12."""

    def __init__(self, number: int) -> None:
        super().__init__(f"Month number {number} must be between 1 and 12")


class DuplicateTopfNameError(FinanceError):
    """Raised when a Topf name is already taken by another Topf."""

    def __init__(self, name: str) -> None:
        super().__init__(f"A Topf named '{name}' already exists")


class SalaryAllocationExceedsSalaryError(FinanceError):
    """Raised when the parts of a SalaryPlan add up to more than the salary."""

    def __init__(self, salary: Decimal, allocated: Decimal) -> None:
        super().__init__(
            f"The salary parts add up to {allocated}, which is "
            f"{allocated - salary} more than the salary of {salary}; "
            "reduce the parts or raise the salary"
        )


class SalaryPartNotFoundError(FinanceError):
    """Raised when a SalaryPlan has no part for the given Topf."""

    def __init__(self, topf_name: str) -> None:
        super().__init__(f"The salary plan has no part for Topf '{topf_name}'")


class SalaryPartItemNotFoundError(FinanceError):
    """Raised when a SalaryPart has no item with the given name."""

    def __init__(self, topf_name: str, item_name: str) -> None:
        super().__init__(
            f"The salary part for Topf '{topf_name}' has no item '{item_name}'"
        )
