from decimal import Decimal

import pytest

from finance_manager.model import (
    Bankkonto,
    Bargeld,
    Kontoart,
    Topf,
    TopfStatus,
    UserConfig,
    Value,
)
from finance_manager.model.errors import (
    DuplicateTopfNameError,
    TopfAlreadyAufgeloestError,
    TopfValueNotZeroError,
)

CONFIG = UserConfig()
SPARBUCH = Bankkonto(CONFIG, "Sparbuch", "ING", Kontoart.SPARBUCH)
SCHUBLADE = Bargeld(CONFIG, "Schublade")


def euro(number: str) -> Value:
    return Value(Decimal(number))


def make_topf(geldort_values: dict[str, Value] | None = None) -> Topf:
    return Topf(
        UserConfig(),
        "Urlaub",
        main_geldort=SPARBUCH,
        geldort_values=dict(geldort_values or {}),
    )


def test_new_topf_is_active() -> None:
    topf = make_topf()

    assert topf.is_active
    assert topf.status is TopfStatus.ACTIVE


def test_new_topf_has_no_geldorte_and_value_zero() -> None:
    topf = make_topf()

    assert topf.geldort_values == {}
    assert topf.get_actual_value() == euro("0")


def test_actual_value_is_sum_of_geldort_values() -> None:
    topf = make_topf(
        {SPARBUCH.identifier: euro("2000.00"), SCHUBLADE.identifier: euro("530.00")}
    )

    assert topf.get_actual_value() == euro("2530.00")


def test_actual_value_can_be_negative() -> None:
    topf = make_topf(
        {SPARBUCH.identifier: euro("100.00"), SCHUBLADE.identifier: euro("-150.00")}
    )

    assert topf.get_actual_value() == euro("-50.00")


def test_add_geldort_value_adds_new_geldort() -> None:
    topf = make_topf({SPARBUCH.identifier: euro("10.00")})

    topf.add_geldort_value(SCHUBLADE, euro("5.00"))

    assert topf.geldort_values == {
        SPARBUCH.identifier: euro("10.00"),
        SCHUBLADE.identifier: euro("5.00"),
    }


def test_add_geldort_value_adds_to_existing_geldort() -> None:
    topf = make_topf({SPARBUCH.identifier: euro("10.00")})

    topf.add_geldort_value(SPARBUCH, euro("20.00"))

    assert topf.geldort_values == {SPARBUCH.identifier: euro("30.00")}


def test_geldort_is_removed_when_its_value_reaches_zero() -> None:
    topf = make_topf(
        {SPARBUCH.identifier: euro("10.00"), SCHUBLADE.identifier: euro("5.00")}
    )

    topf.add_geldort_value(SPARBUCH, euro("-10.00"))

    assert topf.geldort_values == {SCHUBLADE.identifier: euro("5.00")}


def test_geldort_with_zero_is_not_kept_when_creating_topf() -> None:
    topf = make_topf(
        {SPARBUCH.identifier: euro("0"), SCHUBLADE.identifier: euro("5.00")}
    )

    assert topf.geldort_values == {SCHUBLADE.identifier: euro("5.00")}


def test_aufgeloester_topf_is_no_longer_active() -> None:
    topf = make_topf()

    topf.aufloesen()

    assert not topf.is_active


def test_topf_cannot_be_aufgeloest_twice() -> None:
    topf = make_topf()
    topf.aufloesen()

    with pytest.raises(TopfAlreadyAufgeloestError):
        topf.aufloesen()


def test_topf_with_values_adding_up_to_zero_can_be_aufgeloest() -> None:
    topf = make_topf(
        {SPARBUCH.identifier: euro("50.00"), SCHUBLADE.identifier: euro("-50.00")}
    )

    topf.aufloesen()

    assert not topf.is_active


@pytest.mark.parametrize("number", ["250.00", "-30.00"])
def test_topf_with_value_other_than_zero_cannot_be_aufgeloest(number: str) -> None:
    topf = make_topf({SPARBUCH.identifier: euro(number)})

    with pytest.raises(TopfValueNotZeroError):
        topf.aufloesen()

    assert topf.is_active


def test_topf_name_must_be_unique_per_user() -> None:
    config = UserConfig()
    Topf(config, "Urlaub", main_geldort=SPARBUCH)

    with pytest.raises(DuplicateTopfNameError):
        Topf(config, "Urlaub", main_geldort=SCHUBLADE)


def test_same_topf_name_is_allowed_for_different_users() -> None:
    Topf(UserConfig(), "Urlaub", main_geldort=SPARBUCH)

    zweiter_topf = Topf(UserConfig(), "Urlaub", main_geldort=SPARBUCH)

    assert zweiter_topf.name == "Urlaub"
