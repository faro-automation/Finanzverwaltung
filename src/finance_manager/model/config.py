"""UserConfig: per-user state, e.g. counters and names that must be unique."""

from datetime import date

from finance_manager.model.errors import DuplicateTopfNameError


class UserConfig:
    """Everything that belongs to one user and must not be shared between users.

    It holds the counters that number Geldort identifiers, one counter per
    combination of identifier parts, e.g. ("ING", "Tagesgeldkonto"); the
    counters that number RealTransactions, one per month; and the names of
    all Töpfe, because a Topf name identifies the Topf.
    """

    def __init__(self) -> None:
        self._geldort_counters: dict[tuple[str, str], int] = {}
        self._transaction_counters: dict[tuple[int, int], int] = {}
        self._topf_names: set[str] = set()

    def count_up_geldort(self, identifier_parts: tuple[str, str]) -> int:
        """Increase the counter for these Geldort identifier parts; return it."""
        number = self._geldort_counters.get(identifier_parts, 0) + 1
        self._geldort_counters[identifier_parts] = number
        return number

    def count_up_transaction(self, transaction_date: date) -> int:
        """Increase the counter for the month of this date; return it."""
        month = (transaction_date.year, transaction_date.month)
        number = self._transaction_counters.get(month, 0) + 1
        self._transaction_counters[month] = number
        return number

    def register_topf_name(self, name: str) -> None:
        """Reserve a Topf name. Each name can be used only once per user."""
        if name in self._topf_names:
            raise DuplicateTopfNameError(name)
        self._topf_names.add(name)
