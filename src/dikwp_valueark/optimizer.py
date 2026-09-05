from __future__ import annotations

import math
import random
from typing import Any

from .defaults import load_defaults
from .model import (
    PortfolioError,
    compute_metrics,
    constraint_violations,
    holdings_to_weights,
    holdings_total,
    insurance_check,
    liquidity_floor_weight,
    normalize_scenario_weights,
)


def _split_with_caps(
    total: float,
    ids: list[str],
    caps: dict[str, float],
    biases: dict[str, float],
    rng: random.Random,
) -> dict[str, float] | None:
    if total < -1e-12 or total > sum(caps.get(key, 0.0) for key in ids) + 1e-9:
        return None
    remaining = max(0.0, total)
    result = {key: 0.0 for key in ids}
    active = list(ids)
    for _ in range(len(ids) + 4):
        if remaining <= 1e-12:
            break
        if not active:
            return None
        raw: dict[str, float] = {}
        for key in active:
            alpha = max(0.15, 0.5 + 5.0 * max(0.0, biases.get(key, 0.0)))
            raw[key] = rng.gammavariate(alpha, 1.0)
        raw_total = sum(raw.values()) or 1.0
        capped_any = False
        for key in list(active):
            proposed = remaining * raw[key] / raw_total
            room = caps[key] - result[key]
            if proposed >= room - 1e-12:
                result[key] += max(0.0, room)
                remaining -= max(0.0, room)
                active.remove(key)
                capped_any = True
        if not capped_any:
            for key in active:
                result[key] += remaining * raw[key] / raw_total
            remaining = 0.0
            break
    if remaining > 1e-7:
        return None
    return result


def _adjust_template(
    template: dict[str, float],
    *,
    liquidity_floor: float,
    assets: list[dict[str, Any]],
    profile: dict[str, Any],
) -> dict[str, float]:
    """Project a profile template into the declared hard-constraint region.

    Excess risk is redirected to short sovereign instruments and cash.  This is a
    deterministic seed portfolio only; it is not itself a recommendation.
    """
    asset_map = {asset["id"]: asset for asset in assets}
    weights = {asset["id"]: max(0.0, float(template.get(asset["id"], 0.0))) for asset in assets}
    total = sum(weights.values()) or 1.0
    weights = {key: value / total for key, value in weights.items()}

    def redirect(asset_id: str, cap: float) -> None:
        excess = max(0.0, weights.get(asset_id, 0.0) - cap)
        if excess <= 0:
            return
        weights[asset_id] -= excess
        weights["short_gov"] = weights.get("short_gov", 0.0) + 0.70 * excess
        weights["cash"] = weights.get("cash", 0.0) + 0.30 * excess

    redirect("ai_tech", min(float(profile["max_ai"]), float(asset_map["ai_tech"]["max"])))
    redirect("speculative", min(float(profile["max_speculative"]), float(asset_map["speculative"]["max"])))

    equity = weights.get("global_equity", 0.0) + weights.get("ai_tech", 0.0)
    max_equity = float(profile["max_equity"])
    if equity > max_equity:
        excess = equity - max_equity
        ge = weights.get("global_equity", 0.0)
        ai = weights.get("ai_tech", 0.0)
        denom = ge + ai or 1.0
        weights["global_equity"] = max(0.0, ge - excess * ge / denom)
        weights["ai_tech"] = max(0.0, ai - excess * ai / denom)
        weights["short_gov"] += 0.70 * excess
        weights["cash"] += 0.30 * excess

    # Enforce single-asset caps other than the two designated liquidity buckets.
    for asset in assets:
        asset_id = asset["id"]
        if asset_id in {"cash", "short_gov"}:
            continue
        redirect(asset_id, min(float(asset.get("max", 1.0)), float(profile["max_single"])))

    liquidity = weights.get("cash", 0.0) + weights.get("short_gov", 0.0)
    if liquidity < liquidity_floor:
        need = liquidity_floor - liquidity
        donors = [key for key in weights if key not in {"cash", "short_gov"} and weights[key] > 0]
        donor_total = sum(weights[key] for key in donors)
        if donor_total > 1e-12:
            take = min(need, donor_total)
            for key in donors:
                weights[key] -= take * weights[key] / donor_total
            weights["cash"] += 0.45 * take
            weights["short_gov"] += 0.55 * take

    hedge_ids = [asset["id"] for asset in assets if asset.get("group") == "hedge"]
    hedge = sum(weights.get(key, 0.0) for key in hedge_ids)
    hedge_floor = float(profile["min_inflation_hedge"])
    if hedge < hedge_floor:
        need = hedge_floor - hedge
        donors = [key for key in weights if key not in set(hedge_ids) | {"cash"} and weights[key] > 0]
        donor_total = sum(weights[key] for key in donors)
        if donor_total > 1e-12:
            take = min(need, donor_total)
            for key in donors:
                weights[key] -= take * weights[key] / donor_total
            # Use a diversified hedge seed rather than forcing one asset.
            shares = {"inflation_linked": 0.55, "gold": 0.25, "commodities": 0.08, "real_assets": 0.12}
            for key, share in shares.items():
                weights[key] += take * share

    total = sum(max(0.0, value) for value in weights.values()) or 1.0
    return {key: max(0.0, value) / total for key, value in weights.items()}


def _construct_candidate(
    *,
    assets: list[dict[str, Any]],
    profile: dict[str, Any],
    liquidity_floor: float,
    rng: random.Random,
) -> dict[str, float] | None:
    asset_map = {asset["id"]: asset for asset in assets}
    template = profile["template"]
    profile_name = profile.get("name_zh", "")
    liquidity_span = 0.40 if "保值" in profile_name else (0.30 if "平衡" in profile_name else 0.20)
    max_liquidity = min(0.90, max(liquidity_floor, liquidity_floor + liquidity_span))
    # Beta draws keep most candidates near a sensible interior while retaining exploration.
    liquidity = liquidity_floor + (max_liquidity - liquidity_floor) * rng.betavariate(1.3, 2.0)
    remaining = 1.0 - liquidity
    hedge_floor = min(float(profile["min_inflation_hedge"]), remaining)
    hedge_ceiling = min(0.50, remaining)
    hedge = hedge_floor + max(0.0, hedge_ceiling - hedge_floor) * rng.betavariate(1.2, 2.2)
    remaining -= hedge
    speculative = min(float(profile["max_speculative"]), remaining) * rng.betavariate(0.7, 5.0)
    remaining -= speculative
    max_equity = min(float(profile["max_equity"]), remaining)
    template_equity = float(template.get("global_equity", 0.0)) + float(template.get("ai_tech", 0.0))
    equity_center = min(max_equity, template_equity)
    random_equity = max_equity * rng.betavariate(1.7, 1.8)
    equity = min(max_equity, 0.45 * equity_center + 0.55 * random_equity)
    stabilizer = remaining - equity

    result: dict[str, float] = {asset["id"]: 0.0 for asset in assets}
    # Liquidity split.
    liquidity_split = _split_with_caps(
        liquidity,
        ["cash", "short_gov"],
        {"cash": float(asset_map["cash"]["max"]), "short_gov": float(asset_map["short_gov"]["max"])},
        {"cash": float(template.get("cash", 0.0)), "short_gov": float(template.get("short_gov", 0.0))},
        rng,
    )
    if liquidity_split is None:
        return None
    result.update(liquidity_split)

    hedge_ids = ["inflation_linked", "gold", "commodities", "real_assets"]
    hedge_split = _split_with_caps(
        hedge,
        hedge_ids,
        {key: min(float(asset_map[key]["max"]), float(profile["max_single"])) for key in hedge_ids},
        {key: float(template.get(key, 0.0)) for key in hedge_ids},
        rng,
    )
    if hedge_split is None:
        return None
    result.update(hedge_split)

    ai_cap = min(float(profile["max_ai"]), float(asset_map["ai_tech"]["max"]), equity)
    ai_bias_ratio = float(template.get("ai_tech", 0.0)) / max(1e-9, template_equity)
    ai = min(ai_cap, equity * max(0.02, min(0.50, 0.5 * ai_bias_ratio + 0.5 * rng.betavariate(1.2, 3.2))))
    global_equity = equity - ai
    if global_equity > min(float(asset_map["global_equity"]["max"]), float(profile["max_single"])) + 1e-9:
        return None
    result["ai_tech"] = ai
    result["global_equity"] = global_equity

    stabilizer_ids = ["quality_bonds", "foreign_reserve"]
    stabilizer_split = _split_with_caps(
        stabilizer,
        stabilizer_ids,
        {key: min(float(asset_map[key]["max"]), float(profile["max_single"])) for key in stabilizer_ids},
        {key: float(template.get(key, 0.0)) for key in stabilizer_ids},
        rng,
    )
    if stabilizer_split is None:
        return None
    result.update(stabilizer_split)
    result["speculative"] = speculative
    total = sum(result.values())
    if total <= 0:
        return None
    result = {key: value / total for key, value in result.items()}
    if constraint_violations(result, assets=assets, profile=profile, liquidity_floor=liquidity_floor):
        return None
    return result


def _score(metrics: Any, objective: dict[str, float]) -> float:
    return (
        float(objective["worst"]) * metrics.worst_case
        + float(objective["cvar"]) * metrics.cvar_25
        + float(objective["mean"]) * metrics.weighted_mean
        - float(objective["dispersion"]) * metrics.dispersion
        - float(objective["turnover"]) * metrics.turnover
        - float(objective["hhi"]) * metrics.hhi
    )


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * min(1.0, max(0.0, q))
    low = int(math.floor(index))
    high = int(math.ceil(index))
    if low == high:
        return ordered[low]
    fraction = index - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def _rebalance_plan(
    current: dict[str, float],
    target: dict[str, float],
    ranges: dict[str, dict[str, float]],
    *,
    total: float,
    monthly_contribution: float,
    assets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    asset_map = {asset["id"]: asset for asset in assets}
    plan: list[dict[str, Any]] = []
    positive: list[tuple[str, float]] = []
    for asset_id in asset_map:
        current_amount = current.get(asset_id, 0.0) * total
        target_amount = target.get(asset_id, 0.0) * total
        difference = target_amount - current_amount
        lower = ranges[asset_id]["lower"] * total
        upper = ranges[asset_id]["upper"] * total
        if current_amount < lower:
            action = "BUY_OR_ADD"
            positive.append((asset_id, max(0.0, difference)))
        elif current_amount > upper:
            action = "REDUCE_OR_REDIRECT_NEW_MONEY"
        else:
            action = "HOLD_WITHIN_RANGE"
        plan.append({
            "asset_id": asset_id,
            "asset_name_zh": asset_map[asset_id]["name_zh"],
            "current_weight": current.get(asset_id, 0.0),
            "target_weight": target.get(asset_id, 0.0),
            "target_range": ranges[asset_id],
            "current_amount": current_amount,
            "target_amount": target_amount,
            "difference": difference,
            "action": action,
        })
    plan.sort(key=lambda row: abs(row["difference"]), reverse=True)
    contribution_plan: list[dict[str, Any]] = []
    available = max(0.0, monthly_contribution)
    total_positive = sum(value for _, value in positive)
    if available > 0 and total_positive > 0:
        for asset_id, gap in sorted(positive, key=lambda item: item[1], reverse=True):
            amount = min(gap, available * gap / total_positive)
            contribution_plan.append({"asset_id": asset_id, "asset_name_zh": asset_map[asset_id]["name_zh"], "amount": amount})
    return plan, contribution_plan


def _warnings(
    *,
    holdings: dict[str, float],
    current_metrics: Any,
    target_metrics: Any,
    liquidity_floor: float,
    profile: dict[str, Any],
    settings: dict[str, Any],
    insurance: dict[str, Any],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    if current_metrics.liquidity_weight + 1e-9 < liquidity_floor:
        warnings.append({"level":"HIGH","code":"LIQUIDITY_SHORTFALL","message_zh":"当前现金与短期主权工具不足以覆盖声明的应急资金和近期支出。"})
    if not insurance["fully_within_declared_capacity"]:
        warnings.append({"level":"HIGH","code":"INSURANCE_CAPACITY_GAP","message_zh":"现金金额超过用户声明的存款保险容量，或尚未验证保险边界。"})
    if current_metrics.ai_weight > float(profile["max_ai"]) + 1e-9:
        warnings.append({"level":"MEDIUM","code":"AI_CONCENTRATION","message_zh":"AI/科技集中仓超过所选风险档案上限。"})
    if current_metrics.speculative_weight > float(profile["max_speculative"]) + 1e-9:
        warnings.append({"level":"HIGH","code":"SPECULATIVE_CAP","message_zh":"高波动投机仓超过所选风险档案上限。"})
    if max(0.0, float(settings.get("high_interest_debt", 0.0))) > 0 and float(settings.get("debt_apr", 0.0)) >= 0.08:
        warnings.append({"level":"HIGH","code":"HIGH_COST_DEBT_REVIEW","message_zh":"存在高成本债务。市场投资回报不确定，应先单独比较偿债的确定性收益、流动性和税务后果。"})
    if int(settings.get("horizon_years", 10)) < 3 and current_metrics.equity_weight > 0.25:
        warnings.append({"level":"HIGH","code":"SHORT_HORIZON_EQUITY","message_zh":"投资期限较短而权益暴露较高，近期提款可能被迫在回撤中出售。"})
    if target_metrics.worst_case < -0.20:
        warnings.append({"level":"MEDIUM","code":"TARGET_WORST_CASE","message_zh":"即使优化后，所声明压力世界中的最差实际回报仍低于-20%；请重新检查目标、情景和约束。"})
    if not warnings:
        warnings.append({"level":"INFO","code":"NO_PRIMARY_RULE_BREACH","message_zh":"未发现预设硬约束违反；这不意味着没有市场、税务、信用、托管或法律风险。"})
    return warnings


def analyze_and_optimize(portfolio: dict[str, Any], *, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog = defaults or load_defaults()
    assets = catalog["assets"]
    asset_ids = [asset["id"] for asset in assets]
    settings = dict(catalog["default_settings"])
    settings.update(portfolio.get("settings", {}))
    profile_key = settings.get("profile", "balanced")
    if profile_key not in catalog["profiles"]:
        raise PortfolioError(f"Unknown profile: {profile_key}")
    profile = catalog["profiles"][profile_key]
    holdings = {asset_id: max(0.0, float(portfolio.get("holdings", {}).get(asset_id, 0.0))) for asset_id in asset_ids}
    total = holdings_total(holdings)
    current_weights = holdings_to_weights(holdings, asset_ids)
    weights_input = portfolio.get("scenario_weights") or catalog["alert_presets"].get(settings.get("acevo_alert", "yellow"), {})
    scenario_weights = normalize_scenario_weights(weights_input, catalog["scenarios"])
    liq_floor = liquidity_floor_weight(
        total,
        float(settings.get("monthly_expenses", 0.0)),
        float(settings.get("reserve_months", 0.0)),
        float(settings.get("near_term_outflows", 0.0)),
    )
    current_metrics = compute_metrics(
        current_weights,
        current_weights=current_weights,
        assets=assets,
        scenarios=catalog["scenarios"],
        scenario_weights=scenario_weights,
        total_value=total,
        horizon_years=int(settings.get("horizon_years", 10)),
    )

    rng = random.Random(int(settings.get("seed", 95095)))
    candidate_count = max(1000, min(200000, int(settings.get("candidate_count", 25000))))
    candidates: list[tuple[float, dict[str, float], Any]] = []

    template = _adjust_template(profile["template"], liquidity_floor=liq_floor, assets=assets, profile=profile)
    if not constraint_violations(template, assets=assets, profile=profile, liquidity_floor=liq_floor):
        metrics = compute_metrics(template, current_weights=current_weights, assets=assets, scenarios=catalog["scenarios"], scenario_weights=scenario_weights, total_value=total, horizon_years=int(settings.get("horizon_years", 10)))
        candidates.append((_score(metrics, profile["objective"]), template, metrics))
    if not constraint_violations(current_weights, assets=assets, profile=profile, liquidity_floor=liq_floor):
        candidates.append((_score(current_metrics, profile["objective"]), current_weights, current_metrics))

    attempts = 0
    while len(candidates) < candidate_count and attempts < candidate_count * 5:
        attempts += 1
        candidate = _construct_candidate(assets=assets, profile=profile, liquidity_floor=liq_floor, rng=rng)
        if candidate is None:
            continue
        metrics = compute_metrics(candidate, current_weights=current_weights, assets=assets, scenarios=catalog["scenarios"], scenario_weights=scenario_weights, total_value=total, horizon_years=int(settings.get("horizon_years", 10)))
        candidates.append((_score(metrics, profile["objective"]), candidate, metrics))
    if not candidates:
        raise PortfolioError("No feasible portfolio was found. Emergency liquidity need may exceed available assets or constraints may conflict.")
    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_weights, best_metrics = candidates[0]
    near = candidates[: min(250, max(25, len(candidates) // 100))]
    target_ranges: dict[str, dict[str, float]] = {}
    absolute_band = float(profile["no_trade_band"])
    for asset_id in asset_ids:
        samples = [row[1].get(asset_id, 0.0) for row in near]
        lower = _percentile(samples, 0.10)
        upper = _percentile(samples, 0.90)
        target = best_weights.get(asset_id, 0.0)
        lower = max(0.0, min(lower, target - absolute_band * 0.35))
        upper = min(1.0, max(upper, target + absolute_band * 0.35))
        target_ranges[asset_id] = {"lower": lower, "target": target, "upper": upper}

    plan, contribution_plan = _rebalance_plan(
        current_weights,
        best_weights,
        target_ranges,
        total=total,
        monthly_contribution=float(settings.get("monthly_contribution", 0.0)),
        assets=assets,
    )
    insurance = insurance_check(
        holdings,
        insured_limit_per_institution=float(settings.get("insured_limit_per_institution", 0.0)),
        insured_institution_count=int(settings.get("insured_institution_count", 0)),
    )
    warnings = _warnings(
        holdings=holdings,
        current_metrics=current_metrics,
        target_metrics=best_metrics,
        liquidity_floor=liq_floor,
        profile=profile,
        settings=settings,
        insurance=insurance,
    )
    scenario_names = {scenario["id"]: scenario["name_zh"] for scenario in catalog["scenarios"]}
    scenario_outcomes = [
        {
            "scenario_id": scenario_id,
            "scenario_name_zh": scenario_names[scenario_id],
            "importance_weight": scenario_weights[scenario_id],
            "current_real_return": current_metrics.scenario_returns[scenario_id],
            "target_real_return": best_metrics.scenario_returns[scenario_id],
            "target_value_after_scenario": total * max(0.0, 1.0 + best_metrics.scenario_returns[scenario_id]),
        }
        for scenario_id in scenario_weights
    ]
    scenario_outcomes.sort(key=lambda row: row["target_real_return"])
    return {
        "schema": "dikwp-valueark-analysis-1.0",
        "version": "1.0.0",
        "status": "EDUCATIONAL_DECISION_SUPPORT_ONLY",
        "generated_from": portfolio.get("name", "unnamed portfolio"),
        "settings": settings,
        "profile": {"id": profile_key, **profile},
        "portfolio_total": total,
        "liquidity_floor_weight": liq_floor,
        "current_weights": current_weights,
        "target_weights": best_weights,
        "target_ranges": target_ranges,
        "current_metrics": current_metrics.to_dict(),
        "target_metrics": best_metrics.to_dict(),
        "optimizer": {
            "method": "seeded constructive random search under hard constraints",
            "candidate_target": candidate_count,
            "feasible_candidates": len(candidates),
            "attempts": attempts,
            "best_score": best_score,
            "near_optimal_sample": len(near),
            "scenario_weights_are_probabilities": False,
        },
        "scenario_outcomes": scenario_outcomes,
        "rebalance_plan": plan,
        "next_contribution_plan": contribution_plan,
        "insurance_check": insurance,
        "warnings": warnings,
        "market_snapshot": catalog["market_snapshot"],
        "constitutional_invariants": catalog["constitutional_invariants"],
        "limitations": [
            "Broad asset classes are not specific securities and may not be available in every jurisdiction.",
            "Scenario returns and long-run real returns are editable analytical assumptions, not forecasts.",
            "The optimizer does not model individual taxes, benefits, estate planning, currency liabilities, bid-ask spreads or product credit risk.",
            "No trade is executed; all actions require the user and, where appropriate, a licensed professional.",
        ],
    }
