from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class State:
    stage: str
    exported: bool
    automatic_trade_authority: int
    automatic_broker_connection: int
    leverage_allowed: bool
    short_selling_allowed: bool
    specific_security_recommendation: bool


def successors(s: State) -> list[State]:
    out: list[State] = []
    if s.stage == "INPUT":
        out.append(State("ANALYZED", False, 0, 0, False, False, False))
    if s.stage == "ANALYZED":
        out.append(State("PROPOSED", False, 0, 0, False, False, False))
        out.append(State("EXPORTED", True, 0, 0, False, False, False))
    if s.stage == "PROPOSED":
        out.append(State("EXPORTED", True, 0, 0, False, False, False))
    return out


def violations(s: State) -> list[str]:
    failures: list[str] = []
    if s.automatic_trade_authority != 0:
        failures.append("AUTOMATIC_TRADE_AUTHORITY_NONZERO")
    if s.automatic_broker_connection != 0:
        failures.append("BROKER_CONNECTION_NONZERO")
    if s.leverage_allowed:
        failures.append("LEVERAGE_ALLOWED")
    if s.short_selling_allowed:
        failures.append("SHORT_SELLING_ALLOWED")
    if s.specific_security_recommendation:
        failures.append("SPECIFIC_SECURITY_RECOMMENDATION")
    if s.exported and s.stage != "EXPORTED":
        failures.append("EXPORT_FLAG_STAGE_MISMATCH")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="validation/BOUNDED_MODEL_CHECK_RECEIPT.json")
    args = parser.parse_args()
    initial = State("INPUT", False, 0, 0, False, False, False)
    queue = deque([(initial, 0)])
    seen = {initial}
    transitions = 0
    max_depth = 0
    failures: list[dict] = []
    while queue:
        state, depth = queue.popleft()
        max_depth = max(max_depth, depth)
        bad = violations(state)
        if bad:
            failures.append({"state": asdict(state), "violations": bad})
        for nxt in successors(state):
            transitions += 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, depth + 1))
    receipt = {
        "model": "ValueArk bounded action-state abstraction",
        "states": len(seen),
        "transitions_checked": transitions,
        "max_shortest_path_depth": max_depth,
        "violations": failures,
        "passed": not failures,
        "scope_notice": "Finite action-state abstraction only; not a proof for arbitrary deployments or financial outcomes."
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
