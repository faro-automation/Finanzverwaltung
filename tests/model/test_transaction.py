from datetime import date
from decimal import Decimal

import pytest

from finance_manager.model import (
    Auslage,
    Bankkonto,
    Direction,
    Kontoart,
    RealTransaction,
    Topf,
    TopfTransfer,
    Transaction,
    TransactionMark,
    UserConfig,
    Value,
)
from finance_manager.model.errors import (
    SameTopfTransferError,
    TransactionValueNotPositiveError,
)

CONFIG = UserConfig()
GIROKONTO = Bankkonto(CONFIG, "Girokonto", "ING", Kontoart.GIROKONTO)
URLAUB = Topf(CONFIG, "Urlaub", main_geldort=GIROKONTO)
FREIZEIT = Topf(CONFIG, "Freizeit", main_geldort=GIROKONTO)
DAY = date(2026, 3, 5)


def test_real_transaction_with_positive_value_is_incoming() -> None:
    gehalt = RealTransaction(CONFIG, Value(Decimal("3000.00")), DAY, geldort=GIROKONTO)

    assert gehalt.direction is Direction.INCOMING


def test_real_transaction_with_negative_value_is_outgoing() -> None:
    einkauf = RealTransaction(CONFIG, Value(Decimal("-42.50")), DAY, geldort=GIROKONTO)

    assert einkauf.direction is Direction.OUTGOING


def test_real_transaction_and_topf_transfer_are_transactions() -> None:
    einkauf = RealTransaction(CONFIG, Value(Decimal("-42.50")), DAY, geldort=GIROKONTO)
    umbuchung = TopfTransfer(
        Value(Decimal("100.00")), DAY, source=URLAUB, target=FREIZEIT, geldort=GIROKONTO
    )

    assert isinstance(einkauf, Transaction)
    assert isinstance(umbuchung, Transaction)


def test_topf_transfer_keeps_source_and_target() -> None:
    umbuchung = TopfTransfer(
        Value(Decimal("100.00")), DAY, source=URLAUB, target=FREIZEIT, geldort=GIROKONTO
    )

    assert umbuchung.source is URLAUB
    assert umbuchung.target is FREIZEIT


@pytest.mark.parametrize("number", ["0", "-100.00"])
def test_topf_transfer_value_must_be_positive(number: str) -> None:
    with pytest.raises(TransactionValueNotPositiveError):
        TopfTransfer(
            Value(Decimal(number)),
            DAY,
            source=URLAUB,
            target=FREIZEIT,
            geldort=GIROKONTO,
        )


def test_topf_transfer_rejects_same_topf() -> None:
    with pytest.raises(SameTopfTransferError):
        TopfTransfer(
            Value(Decimal("100.00")),
            DAY,
            source=URLAUB,
            target=URLAUB,
            geldort=GIROKONTO,
        )


def test_real_transaction_keeps_statement_text() -> None:
    einkauf = RealTransaction(
        CONFIG,
        Value(Decimal("-42.50")),
        DAY,
        geldort=GIROKONTO,
        statement_text="SUPERMARKT",
    )

    assert einkauf.statement_text == "SUPERMARKT"


def test_real_transaction_is_not_marked_by_default() -> None:
    einkauf = RealTransaction(CONFIG, Value(Decimal("-42.50")), DAY, geldort=GIROKONTO)

    assert einkauf.get_mark() is None


def test_real_transaction_can_be_marked_as_auslage_or_rueckzahlung() -> None:
    auslage = RealTransaction(
        CONFIG,
        Value(Decimal("-20.00")),
        DAY,
        geldort=GIROKONTO,
        mark=TransactionMark.AUSLAGE,
    )
    rueckzahlung = RealTransaction(
        CONFIG,
        Value(Decimal("20.00")),
        DAY,
        geldort=GIROKONTO,
        mark=TransactionMark.RUECKZAHLUNG,
    )

    assert auslage.get_mark() is TransactionMark.AUSLAGE
    assert rueckzahlung.get_mark() is TransactionMark.RUECKZAHLUNG


def test_topf_transfer_keeps_shared_geldort() -> None:
    umbuchung = TopfTransfer(
        Value(Decimal("100.00")),
        DAY,
        source=URLAUB,
        target=FREIZEIT,
        geldort=GIROKONTO,
    )

    assert umbuchung.geldort is GIROKONTO


def make_payment(number: str, mark: TransactionMark) -> RealTransaction:
    return RealTransaction(
        CONFIG, Value(Decimal(number)), DAY, geldort=GIROKONTO, mark=mark
    )


def test_new_auslage_expects_one_rueckzahlung_and_is_open() -> None:
    auslage = Auslage(make_payment("-50.00", TransactionMark.AUSLAGE))

    assert auslage.expected_rueckzahlung_amount == 1
    assert not auslage.has_rueckzahlung
    assert auslage.is_open


def test_auslage_is_closed_after_expected_rueckzahlung_whatever_its_value() -> None:
    auslage = Auslage(make_payment("-50.00", TransactionMark.AUSLAGE))

    auslage.add_rueckzahlung(make_payment("20.00", TransactionMark.RUECKZAHLUNG))

    assert auslage.has_rueckzahlung
    assert not auslage.is_open


def test_auslage_stays_open_until_all_expected_rueckzahlungen_arrived() -> None:
    auslage = Auslage(
        make_payment("-90.00", TransactionMark.AUSLAGE), expected_rueckzahlung_amount=2
    )

    auslage.add_rueckzahlung(make_payment("30.00", TransactionMark.RUECKZAHLUNG))
    assert auslage.is_open

    auslage.add_rueckzahlung(make_payment("40.00", TransactionMark.RUECKZAHLUNG))
    assert not auslage.is_open
    assert len(auslage.rueckzahlungen) == 2


def test_real_transaction_identifier_counts_up_per_month() -> None:
    config = UserConfig()

    erste = RealTransaction(
        config, Value(Decimal("-1.00")), date(2026, 3, 5), GIROKONTO
    )
    zweite = RealTransaction(
        config, Value(Decimal("-2.00")), date(2026, 3, 9), GIROKONTO
    )
    april = RealTransaction(
        config, Value(Decimal("-3.00")), date(2026, 4, 1), GIROKONTO
    )

    assert erste.identifier == "2026_03_0001"
    assert zweite.identifier == "2026_03_0002"
    assert april.identifier == "2026_04_0001"


def test_identical_transactions_get_different_identifiers() -> None:
    config = UserConfig()

    erstes_broetchen = RealTransaction(config, Value(Decimal("-3.50")), DAY, GIROKONTO)
    zweites_broetchen = RealTransaction(config, Value(Decimal("-3.50")), DAY, GIROKONTO)

    assert erstes_broetchen.identifier != zweites_broetchen.identifier
