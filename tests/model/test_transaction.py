from datetime import date
from decimal import Decimal

import pytest

from finance_manager.model import (
    Auslage,
    Bankkonto,
    Bargeld,
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
    SplitGeldortMismatchError,
    SplitSourceMismatchError,
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
        CONFIG,
        Value(Decimal("100.00")),
        DAY,
        source=URLAUB,
        target=FREIZEIT,
        geldort=GIROKONTO,
    )

    assert isinstance(einkauf, Transaction)
    assert isinstance(umbuchung, Transaction)


def test_topf_transfer_keeps_source_and_target() -> None:
    umbuchung = TopfTransfer(
        CONFIG,
        Value(Decimal("100.00")),
        DAY,
        source=URLAUB,
        target=FREIZEIT,
        geldort=GIROKONTO,
    )

    assert umbuchung.source is URLAUB
    assert umbuchung.target is FREIZEIT


@pytest.mark.parametrize("number", ["0", "-100.00"])
def test_topf_transfer_value_must_be_positive(number: str) -> None:
    with pytest.raises(TransactionValueNotPositiveError):
        TopfTransfer(
            CONFIG,
            Value(Decimal(number)),
            DAY,
            source=URLAUB,
            target=FREIZEIT,
            geldort=GIROKONTO,
        )


def test_topf_transfer_rejects_same_topf() -> None:
    with pytest.raises(SameTopfTransferError):
        TopfTransfer(
            CONFIG,
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
        CONFIG,
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


def test_real_transaction_has_no_topf_by_default() -> None:
    einkauf = RealTransaction(CONFIG, Value(Decimal("-42.50")), DAY, GIROKONTO)

    assert einkauf.topf is None


def test_real_transaction_can_get_topf_when_created() -> None:
    einkauf = RealTransaction(
        CONFIG, Value(Decimal("-42.50")), DAY, GIROKONTO, topf=FREIZEIT
    )

    assert einkauf.topf is FREIZEIT


def test_assign_topf_replaces_earlier_topf() -> None:
    einkauf = RealTransaction(
        CONFIG, Value(Decimal("-42.50")), DAY, GIROKONTO, topf=FREIZEIT
    )

    einkauf.assign_topf(URLAUB)

    assert einkauf.topf is URLAUB


def test_plain_topf_transfer_splits_nothing() -> None:
    umschichtung = TopfTransfer(
        CONFIG,
        Value(Decimal("100.00")),
        DAY,
        source=URLAUB,
        target=FREIZEIT,
        geldort=GIROKONTO,
    )

    assert umschichtung.split_of is None


def test_topf_transfer_can_split_a_real_transaction() -> None:
    einkauf = RealTransaction(
        CONFIG, Value(Decimal("-42.50")), DAY, GIROKONTO, topf=URLAUB
    )

    aufteilung = TopfTransfer(
        CONFIG,
        Value(Decimal("12.50")),
        DAY,
        source=URLAUB,
        target=FREIZEIT,
        geldort=GIROKONTO,
        split_of=einkauf,
    )

    assert aufteilung.split_of is einkauf


def test_topf_transfer_identifier_uses_month_and_source_topf() -> None:
    config = UserConfig()

    erste = TopfTransfer(
        config, Value(Decimal("10.00")), DAY, URLAUB, FREIZEIT, GIROKONTO
    )
    zweite = TopfTransfer(
        config, Value(Decimal("20.00")), DAY, URLAUB, FREIZEIT, GIROKONTO
    )
    andere_quelle = TopfTransfer(
        config, Value(Decimal("5.00")), DAY, FREIZEIT, URLAUB, GIROKONTO
    )

    assert erste.identifier == "2026_03_Urlaub_0001"
    assert zweite.identifier == "2026_03_Urlaub_0002"
    assert andere_quelle.identifier == "2026_03_Freizeit_0001"


def test_split_must_start_from_the_topf_of_the_transaction() -> None:
    einkauf = RealTransaction(
        CONFIG, Value(Decimal("-42.50")), DAY, GIROKONTO, topf=URLAUB
    )

    with pytest.raises(SplitSourceMismatchError):
        TopfTransfer(
            CONFIG,
            Value(Decimal("12.50")),
            DAY,
            source=FREIZEIT,
            target=URLAUB,
            geldort=GIROKONTO,
            split_of=einkauf,
        )


def test_split_must_be_on_the_geldort_of_the_transaction() -> None:
    schublade = Bargeld(CONFIG, "Schublade")
    einkauf = RealTransaction(
        CONFIG, Value(Decimal("-42.50")), DAY, GIROKONTO, topf=URLAUB
    )

    with pytest.raises(SplitGeldortMismatchError):
        TopfTransfer(
            CONFIG,
            Value(Decimal("12.50")),
            DAY,
            source=URLAUB,
            target=FREIZEIT,
            geldort=schublade,
            split_of=einkauf,
        )
