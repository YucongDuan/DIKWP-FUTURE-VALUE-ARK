import pytest

from dikwp_valueark.defaults import load_defaults
from dikwp_valueark.model import (
    PortfolioError,
    compute_metrics,
    holdings_to_weights,
    insurance_check,
    liquidity_floor_weight,
    normalize_scenario_weights,
    normalize_weights,
    weighted_cvar_lower,
)


def test_normalize_and_zero_rejection():
    assert normalize_weights({"a": 2, "b": 2}, ["a", "b"]) == {"a": 0.5, "b": 0.5}
    with pytest.raises(PortfolioError):
        normalize_weights({"a": 0}, ["a"])


def test_liquidity_floor():
    assert liquidity_floor_weight(1_000_000, 12_000, 12, 50_000) == pytest.approx(0.194)
    assert liquidity_floor_weight(100_000, 100_000, 12, 0) == pytest.approx(0.95)


def test_weighted_cvar():
    values = {"bad": -0.2, "middle": 0.0, "good": 0.2}
    weights = {"bad": 0.2, "middle": 0.3, "good": 0.5}
    assert weighted_cvar_lower(values, weights, 0.25) == pytest.approx(-0.16)


def test_metrics_charge_fees_and_keep_scenario_keys():
    data = load_defaults()
    assets = data["assets"]
    holdings = {a["id"]: a["default_amount"] for a in assets}
    ids = [a["id"] for a in assets]
    weights = holdings_to_weights(holdings, ids)
    sw = normalize_scenario_weights(data["alert_presets"]["yellow"], data["scenarios"])
    m = compute_metrics(
        weights,
        current_weights=weights,
        assets=assets,
        scenarios=data["scenarios"],
        scenario_weights=sw,
        total_value=sum(holdings.values()),
        horizon_years=10,
    )
    assert set(m.scenario_returns) == {s["id"] for s in data["scenarios"]}
    assert m.annual_fee > 0
    assert m.turnover == pytest.approx(0)
    assert m.real_wealth_floor < sum(holdings.values())


def test_insurance_capacity_is_user_declared():
    check = insurance_check({"cash": 1_200_000}, insured_limit_per_institution=500_000, insured_institution_count=2)
    assert check["declared_insurance_capacity"] == 1_000_000
    assert check["potentially_uninsured_or_unverified"] == 200_000
    assert check["fully_within_declared_capacity"] is False
