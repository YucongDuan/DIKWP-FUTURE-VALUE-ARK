from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

EPS = 1e-12


class PortfolioError(ValueError):
    pass


@dataclass(frozen=True)
class PortfolioMetrics:
    scenario_returns: dict[str, float]
    weighted_mean: float
    worst_case: float
    cvar_25: float
    dispersion: float
    long_run_real: float
    turnover: float
    hhi: float
    annual_fee: float
    liquidity_weight: float
    inflation_hedge_weight: float
    equity_weight: float
    ai_weight: float
    speculative_weight: float
    real_wealth_floor: float
    horizon_value_real: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_returns": self.scenario_returns,
            "weighted_mean": self.weighted_mean,
            "worst_case": self.worst_case,
            "cvar_25": self.cvar_25,
            "dispersion": self.dispersion,
            "long_run_real": self.long_run_real,
            "turnover": self.turnover,
            "hhi": self.hhi,
            "annual_fee": self.annual_fee,
            "liquidity_weight": self.liquidity_weight,
            "inflation_hedge_weight": self.inflation_hedge_weight,
            "equity_weight": self.equity_weight,
            "ai_weight": self.ai_weight,
            "speculative_weight": self.speculative_weight,
            "real_wealth_floor": self.real_wealth_floor,
            "declared_scenario_wealth_floor": self.real_wealth_floor,
            "horizon_value_real": self.horizon_value_real,
        }


def normalize_weights(values: dict[str, float], asset_ids: Iterable[str]) -> dict[str, float]:
    clean = {asset_id: max(0.0, float(values.get(asset_id, 0.0))) for asset_id in asset_ids}
    total = sum(clean.values())
    if total <= EPS:
        raise PortfolioError("Portfolio total must be positive.")
    return {key: value / total for key, value in clean.items()}


def holdings_total(holdings: dict[str, float]) -> float:
    total = sum(max(0.0, float(value)) for value in holdings.values())
    if total <= EPS:
        raise PortfolioError("Holdings must have a positive total value.")
    return total


def holdings_to_weights(holdings: dict[str, float], asset_ids: Iterable[str]) -> dict[str, float]:
    total = holdings_total(holdings)
    return {asset_id: max(0.0, float(holdings.get(asset_id, 0.0))) / total for asset_id in asset_ids}


def normalize_scenario_weights(weights: dict[str, float], scenarios: list[dict[str, Any]]) -> dict[str, float]:
    clean = {scenario["id"]: max(0.0, float(weights.get(scenario["id"], scenario.get("weight", 0.0)))) for scenario in scenarios}
    total = sum(clean.values())
    if total <= EPS:
        return {scenario["id"]: 1.0 / len(scenarios) for scenario in scenarios}
    return {key: value / total for key, value in clean.items()}


def liquidity_floor_weight(total: float, monthly_expenses: float, reserve_months: float, near_term_outflows: float) -> float:
    need = max(0.0, monthly_expenses) * max(0.0, reserve_months) + max(0.0, near_term_outflows)
    return min(0.95, need / total) if total > EPS else 0.95


def weighted_cvar_lower(values: dict[str, float], weights: dict[str, float], alpha: float = 0.25) -> float:
    if not values:
        return 0.0
    ordered = sorted(values.items(), key=lambda item: item[1])
    target = max(EPS, min(1.0, alpha))
    used = 0.0
    aggregate = 0.0
    for key, value in ordered:
        available = max(0.0, weights.get(key, 0.0))
        take = min(available, target - used)
        if take > 0:
            aggregate += take * value
            used += take
        if used + EPS >= target:
            break
    if used <= EPS:
        return ordered[0][1]
    return aggregate / used


def weighted_mean_and_std(values: dict[str, float], weights: dict[str, float]) -> tuple[float, float]:
    mean = sum(weights.get(key, 0.0) * value for key, value in values.items())
    variance = sum(weights.get(key, 0.0) * (value - mean) ** 2 for key, value in values.items())
    return mean, math.sqrt(max(0.0, variance))


def group_weight(weights: dict[str, float], assets: list[dict[str, Any]], groups: set[str]) -> float:
    return sum(weights.get(asset["id"], 0.0) for asset in assets if asset.get("group") in groups)


def compute_metrics(
    weights: dict[str, float],
    *,
    current_weights: dict[str, float],
    assets: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    scenario_weights: dict[str, float],
    total_value: float,
    horizon_years: int,
) -> PortfolioMetrics:
    asset_map = {asset["id"]: asset for asset in assets}
    annual_fee = sum(weights.get(asset_id, 0.0) * float(asset_map[asset_id].get("annual_fee", 0.0)) for asset_id in asset_map)
    scenario_returns: dict[str, float] = {}
    for scenario in scenarios:
        gross = sum(weights.get(asset_id, 0.0) * float(scenario["returns"].get(asset_id, 0.0)) for asset_id in asset_map)
        scenario_returns[scenario["id"]] = gross - annual_fee
    mean, dispersion = weighted_mean_and_std(scenario_returns, scenario_weights)
    worst = min(scenario_returns.values()) if scenario_returns else 0.0
    cvar = weighted_cvar_lower(scenario_returns, scenario_weights, 0.25)
    long_run = sum(weights.get(asset_id, 0.0) * float(asset_map[asset_id].get("long_run_real", 0.0)) for asset_id in asset_map) - annual_fee
    turnover = 0.5 * sum(abs(weights.get(asset_id, 0.0) - current_weights.get(asset_id, 0.0)) for asset_id in asset_map)
    hhi = sum(weight * weight for weight in weights.values())
    liquidity = group_weight(weights, assets, {"liquidity"})
    hedge = group_weight(weights, assets, {"hedge"})
    equity = group_weight(weights, assets, {"equity"})
    ai_weight = weights.get("ai_tech", 0.0)
    speculative = weights.get("speculative", 0.0)
    real_wealth_floor = total_value * max(0.0, 1.0 + worst)
    horizon = max(1, int(horizon_years))
    horizon_value = total_value * max(0.0, (1.0 + long_run) ** horizon)
    return PortfolioMetrics(
        scenario_returns=scenario_returns,
        weighted_mean=mean,
        worst_case=worst,
        cvar_25=cvar,
        dispersion=dispersion,
        long_run_real=long_run,
        turnover=turnover,
        hhi=hhi,
        annual_fee=annual_fee,
        liquidity_weight=liquidity,
        inflation_hedge_weight=hedge,
        equity_weight=equity,
        ai_weight=ai_weight,
        speculative_weight=speculative,
        real_wealth_floor=real_wealth_floor,
        horizon_value_real=horizon_value,
    )


def constraint_violations(
    weights: dict[str, float],
    *,
    assets: list[dict[str, Any]],
    profile: dict[str, Any],
    liquidity_floor: float,
) -> list[str]:
    violations: list[str] = []
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        violations.append("WEIGHTS_DO_NOT_SUM_TO_ONE")
    if any(value < -EPS for value in weights.values()):
        violations.append("NEGATIVE_WEIGHT_OR_LEVERAGE")
    liquidity = group_weight(weights, assets, {"liquidity"})
    hedge = group_weight(weights, assets, {"hedge"})
    equity = group_weight(weights, assets, {"equity"})
    if liquidity + 1e-9 < liquidity_floor:
        violations.append("LIQUIDITY_FLOOR_NOT_MET")
    if hedge + 1e-9 < float(profile["min_inflation_hedge"]):
        violations.append("INFLATION_HEDGE_FLOOR_NOT_MET")
    if equity - 1e-9 > float(profile["max_equity"]):
        violations.append("EQUITY_CAP_EXCEEDED")
    if weights.get("ai_tech", 0.0) - 1e-9 > float(profile["max_ai"]):
        violations.append("AI_CONCENTRATION_CAP_EXCEEDED")
    if weights.get("speculative", 0.0) - 1e-9 > float(profile["max_speculative"]):
        violations.append("SPECULATIVE_CAP_EXCEEDED")
    for asset in assets:
        asset_id = asset["id"]
        cap = float(asset.get("max", 1.0))
        if asset_id not in {"cash", "short_gov"}:
            cap = min(cap, float(profile["max_single"]))
        if weights.get(asset_id, 0.0) - 1e-9 > cap:
            violations.append(f"ASSET_CAP_EXCEEDED:{asset_id}")
    return violations


def insurance_check(
    holdings: dict[str, float],
    *,
    insured_limit_per_institution: float,
    insured_institution_count: int,
) -> dict[str, Any]:
    cash = max(0.0, float(holdings.get("cash", 0.0)))
    capacity = max(0.0, float(insured_limit_per_institution)) * max(0, int(insured_institution_count))
    uninsured = max(0.0, cash - capacity) if capacity > 0 else cash
    return {
        "cash_amount": cash,
        "declared_insurance_capacity": capacity,
        "potentially_uninsured_or_unverified": uninsured,
        "fully_within_declared_capacity": uninsured <= EPS,
        "notice": "Coverage depends on institution eligibility, ownership category, account type, accrued interest and jurisdiction. The software does not verify accounts.",
    }
