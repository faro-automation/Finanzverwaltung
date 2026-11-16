from decimal import Decimal

import pytest

from finance_manager.model import (
    Bankkonto,
    Kontoart,
    Month,
    Salary,
    SalaryPart,
    SalaryPartItem,
    SalaryPlan,
    Topf,
    UserConfig,
    Value,
)
from finance_manager.model.errors import (
    SalaryAllocationExceedsSalaryError,
    SalaryPartItemNotFoundError,
    SalaryPartNotFoundError,
)

CONFIG = UserConfig()
GIROKONTO = Bankkonto(CONFIG, "Girokonto", "ING", Kontoart.GIROKONTO)
SPARBUCH = Bankkonto(CONFIG, "Sparbuch", "VB", Kontoart.SPARBUCH)
VERSICHERUNGEN = Topf(CONFIG, "Versicherungen", main_geldort=GIROKONTO)
URLAUB = Topf(CONFIG, "Urlaub", main_geldort=SPARBUCH)
GEHALT = Topf(CONFIG, "Gehalt", main_geldort=GIROKONTO)
FREIZEIT = Topf(CONFIG, "Freizeit", main_geldort=GIROKONTO)


def euro(number: str) -> Value:
    return Value(Decimal(number))


def make_versicherungen_part() -> SalaryPart:
    return SalaryPart(
        VERSICHERUNGEN,
        GIROKONTO,
        items=(
            SalaryPartItem("KFZ", euro("260.00")),
            SalaryPartItem("Haftpflicht", euro("10.00")),
            SalaryPartItem("Hausrat", euro("20.00")),
        ),
    )


def make_salary(number: str) -> Salary:
    return Salary(euro(number), geldort=GIROKONTO, topf=GEHALT)


def test_salary_plan_keeps_salary_remainder_topf_and_valid_from() -> None:
    plan = SalaryPlan(make_salary("3000.00"), FREIZEIT, valid_from=Month(2027, 1))

    assert plan.salary.value == euro("3000.00")
    assert plan.salary.geldort is GIROKONTO
    assert plan.salary.topf is GEHALT
    assert plan.remainder_topf is FREIZEIT
    assert plan.valid_from == Month(2027, 1)
    assert plan.allocation == ()


def test_salary_part_has_topf_and_geldort() -> None:
    plan = SalaryPlan(
        make_salary("3000.00"),
        FREIZEIT,
        valid_from=Month(2027, 1),
        allocation=(
            make_versicherungen_part(),
            SalaryPart(URLAUB, SPARBUCH, (SalaryPartItem("Urlaub", euro("350.00")),)),
        ),
    )

    urlaub_part = plan.allocation[1]
    assert urlaub_part.topf is URLAUB
    assert urlaub_part.geldort is SPARBUCH
    assert urlaub_part.geldort != plan.salary.geldort


def test_salary_part_without_items_has_value_zero() -> None:
    assert SalaryPart(URLAUB, SPARBUCH).get_value() == euro("0")


def test_salary_part_value_is_sum_of_its_items() -> None:
    assert make_versicherungen_part().get_value() == euro("290.00")


def make_plan(salary: str, *parts: SalaryPart) -> SalaryPlan:
    return SalaryPlan(
        make_salary(salary), FREIZEIT, valid_from=Month(2027, 1), allocation=parts
    )


def test_allocated_and_remainder_value() -> None:
    plan = make_plan("3000.00", make_versicherungen_part())

    assert plan.get_allocated_value() == euro("290.00")
    assert plan.get_remainder_value() == euro("2710.00")


def test_allocation_may_use_the_whole_salary() -> None:
    plan = make_plan("290.00", make_versicherungen_part())

    assert plan.get_remainder_value() == euro("0.00")


def test_plan_with_allocation_above_salary_cannot_be_created() -> None:
    with pytest.raises(SalaryAllocationExceedsSalaryError):
        make_plan("100.00", make_versicherungen_part())


def test_change_item_value_changes_part_and_remainder() -> None:
    plan = make_plan("3000.00", make_versicherungen_part())

    plan.change_item_value(VERSICHERUNGEN, "Haftpflicht", euro("12.50"))

    assert plan.get_allocated_value() == euro("292.50")
    assert plan.get_remainder_value() == euro("2707.50")


def test_add_and_remove_item() -> None:
    plan = make_plan("3000.00", make_versicherungen_part())

    plan.add_item(VERSICHERUNGEN, SalaryPartItem("Rechtsschutz", euro("25.00")))
    plan.remove_item(VERSICHERUNGEN, "KFZ")

    assert plan.get_allocated_value() == euro("55.00")


def test_add_and_remove_part() -> None:
    plan = make_plan("3000.00", make_versicherungen_part())
    urlaub_part = SalaryPart(URLAUB, SPARBUCH, (SalaryPartItem("Urlaub", euro("350")),))

    plan.add_part(urlaub_part)
    assert plan.get_allocated_value() == euro("640.00")

    plan.remove_part(VERSICHERUNGEN)
    assert plan.allocation == (urlaub_part,)


def test_change_that_exceeds_salary_is_rejected_and_undone() -> None:
    plan = make_plan("300.00", make_versicherungen_part())

    with pytest.raises(SalaryAllocationExceedsSalaryError):
        plan.change_item_value(VERSICHERUNGEN, "KFZ", euro("500.00"))

    assert plan.get_allocated_value() == euro("290.00")


def test_lowering_salary_below_allocation_is_rejected_and_undone() -> None:
    plan = make_plan("300.00", make_versicherungen_part())

    with pytest.raises(SalaryAllocationExceedsSalaryError):
        plan.change_salary_value(euro("200.00"))

    assert plan.salary.value == euro("300.00")


def test_adding_part_that_exceeds_salary_is_rejected_and_undone() -> None:
    plan = make_plan("300.00", make_versicherungen_part())
    zu_viel = SalaryPart(URLAUB, SPARBUCH, (SalaryPartItem("Urlaub", euro("350")),))

    with pytest.raises(SalaryAllocationExceedsSalaryError):
        plan.add_part(zu_viel)

    assert len(plan.allocation) == 1


def test_unknown_topf_or_item_raises_error() -> None:
    plan = make_plan("3000.00", make_versicherungen_part())

    with pytest.raises(SalaryPartNotFoundError):
        plan.remove_part(URLAUB)
    with pytest.raises(SalaryPartItemNotFoundError):
        plan.remove_item(VERSICHERUNGEN, "Gibt es nicht")
