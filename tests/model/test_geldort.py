from decimal import Decimal

import pytest

from finance_manager.model import (
    Bankkonto,
    Bargeld,
    GeldortStatus,
    Gutscheine,
    Kontoart,
    UserConfig,
    Value,
)
from finance_manager.model.errors import (
    GeldortAlreadyClosedError,
    GeldortValueNotZeroError,
)


def test_bankkonto_identifier_combines_bank_kontoart_and_number() -> None:
    girokonto = Bankkonto(UserConfig(), "Alltag", "ING", Kontoart.GIROKONTO)

    assert girokonto.identifier == "ING_Girokonto_01"


def test_number_counts_up_per_bank_and_kontoart() -> None:
    config = UserConfig()

    erstes = Bankkonto(config, "Reserve", "ING", Kontoart.TAGESGELDKONTO)
    zweites = Bankkonto(config, "Urlaub", "ING", Kontoart.TAGESGELDKONTO)

    assert erstes.identifier == "ING_Tagesgeldkonto_01"
    assert zweites.identifier == "ING_Tagesgeldkonto_02"


def test_other_kontoart_or_bank_starts_at_one() -> None:
    config = UserConfig()
    Bankkonto(config, "Reserve", "ING", Kontoart.TAGESGELDKONTO)

    festgeld = Bankkonto(config, "Anlage", "ING", Kontoart.FESTGELDKONTO)
    andere_bank = Bankkonto(config, "Anlage", "VB", Kontoart.TAGESGELDKONTO)

    assert festgeld.identifier == "ING_Festgeldkonto_01"
    assert andere_bank.identifier == "VB_Tagesgeldkonto_01"


def test_each_user_config_counts_separately() -> None:
    erster_nutzer = UserConfig()
    zweiter_nutzer = UserConfig()
    Bankkonto(erster_nutzer, "Alltag", "ING", Kontoart.GIROKONTO)

    konto = Bankkonto(zweiter_nutzer, "Alltag", "ING", Kontoart.GIROKONTO)

    assert konto.identifier == "ING_Girokonto_01"


def test_bargeld_identifier_uses_chosen_name() -> None:
    config = UserConfig()

    erste = Bargeld(config, "Schublade")
    zweite = Bargeld(config, "Schublade")

    assert erste.identifier == "Bargeld_Schublade_01"
    assert zweite.identifier == "Bargeld_Schublade_02"


def test_gutscheine_identifier_uses_chosen_name() -> None:
    gutscheine = Gutscheine(UserConfig(), "Geburtstag")

    assert gutscheine.identifier == "Gutscheine_Geburtstag_01"


def test_two_geldorte_with_same_name_are_different() -> None:
    config = UserConfig()

    erstes = Bankkonto(config, "Konto", "ING", Kontoart.GIROKONTO)
    zweites = Bankkonto(config, "Konto", "ING", Kontoart.GIROKONTO)

    assert erstes != zweites


def test_new_geldort_has_actual_value_zero() -> None:
    schublade = Bargeld(UserConfig(), "Schublade")

    assert schublade.get_actual_value() == Value(Decimal(0))


def test_actual_value_can_be_set_for_first_setup() -> None:
    girokonto = Bankkonto(UserConfig(), "Alltag", "ING", Kontoart.GIROKONTO)

    girokonto.set_actual_value(Value(Decimal("1840.00")))

    assert girokonto.get_actual_value() == Value(Decimal("1840.00"))


def test_new_geldort_is_active() -> None:
    konto = Bankkonto(UserConfig(), "Alltag", "ING", Kontoart.GIROKONTO)

    assert konto.is_active
    assert konto.status is GeldortStatus.ACTIVE


def test_geldort_at_zero_can_be_closed_and_keeps_identifier() -> None:
    konto = Bankkonto(UserConfig(), "Alltag", "ING", Kontoart.GIROKONTO)

    konto.close()

    assert not konto.is_active
    assert konto.identifier == "ING_Girokonto_01"


@pytest.mark.parametrize("number", ["10.00", "-10.00"])
def test_geldort_with_value_other_than_zero_cannot_be_closed(number: str) -> None:
    konto = Bankkonto(UserConfig(), "Alltag", "ING", Kontoart.GIROKONTO)
    konto.set_actual_value(Value(Decimal(number)))

    with pytest.raises(GeldortValueNotZeroError):
        konto.close()

    assert konto.is_active


def test_geldort_cannot_be_closed_twice() -> None:
    konto = Bankkonto(UserConfig(), "Alltag", "ING", Kontoart.GIROKONTO)
    konto.close()

    with pytest.raises(GeldortAlreadyClosedError):
        konto.close()


def test_closed_geldort_identifier_is_not_reused() -> None:
    config = UserConfig()
    altes_konto = Bankkonto(config, "Alt", "ING", Kontoart.GIROKONTO)
    altes_konto.close()

    neues_konto = Bankkonto(config, "Neu", "ING", Kontoart.GIROKONTO)

    assert neues_konto.identifier == "ING_Girokonto_02"
