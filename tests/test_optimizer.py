import copy

import pytest

from dikwp_valueark.defaults import load_defaults
from dikwp_valueark.model import constraint_violations
from dikwp_valueark.optimizer import analyze_and_optimize


def sample(candidate_count: int = 3000):
    d = load_defaults()
    settings = copy.deepcopy(d["default_settings"])
    settings["candidate_count"] = candidate_count
    return d, {
        "schema": "dikwp-valueark-portfolio-1.0",
        "name": "test synthetic portfolio",
        "settings": settings,
        "holdings": {a["id"]: a["default_amount"] for a in d["assets"]},
        "scenario_weights": d["alert_presets"]["yellow"],
    }


def test_optimizer_is_deterministic_and_feasible():
    d, p = sample()
    a = analyze_and_optimize(p, defaults=d)
    b = analyze_and_optimize(p, defaults=d)
    assert a["target_weights"] == b["target_weights"]
    assert a["optimizer"]["feasible_candidates"] == 3000
    profile = d["profiles"]["balanced"]
    assert not constraint_violations(
        a["target_weights"], assets=d["assets"], profile=profile,
        liquidity_floor=a["liquidity_floor_weight"]
    )
    assert abs(sum(a["target_weights"].values()) - 1) < 1e-8
    assert a["target_metrics"]["worst_case"] >= a["current_metrics"]["worst_case"]
    assert a["target_metrics"]["worst_case"] < 0  # correlation/custody-break scenario prevents a no-loss illusion
    assert a["constitutional_invariants"]["automatic_trade_authority"] == 0


def test_preservation_profile_forbids_speculative_sleeve():
    d, p = sample(2000)
    p["settings"]["profile"] = "preservation"
    result = analyze_and_optimize(p, defaults=d)
    assert result["target_weights"]["speculative"] == pytest.approx(0, abs=1e-9)
    assert result["target_metrics"]["equity_weight"] <= 0.30 + 1e-9
    assert result["target_metrics"]["ai_weight"] <= 0.08 + 1e-9


def test_liquidity_warning_and_debt_warning():
    d, p = sample(1500)
    p["holdings"] = {a["id"]: 0 for a in d["assets"]}
    p["holdings"]["global_equity"] = 1_000_000
    p["settings"]["high_interest_debt"] = 100_000
    p["settings"]["debt_apr"] = 0.18
    result = analyze_and_optimize(p, defaults=d)
    codes = {w["code"] for w in result["warnings"]}
    assert "LIQUIDITY_SHORTFALL" in codes
    assert "HIGH_COST_DEBT_REVIEW" in codes


def test_scenario_weights_are_never_labelled_probabilities():
    d, p = sample(1200)
    result = analyze_and_optimize(p, defaults=d)
    assert result["optimizer"]["scenario_weights_are_probabilities"] is False
