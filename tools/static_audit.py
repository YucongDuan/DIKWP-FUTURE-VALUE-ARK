from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "dikwp_valueark"
BANNED_IMPORTS = {
    "requests", "httpx", "urllib3", "socket", "paramiko", "selenium",
    "playwright", "ccxt", "alpaca_trade_api", "ib_insync", "subprocess"
}
BANNED_CALLS = {"eval", "exec", "compile", "__import__"}
findings: list[dict[str, object]] = []
files = sorted(SRC.rglob("*.py"))
for path in files:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BANNED_IMPORTS:
                    findings.append({"file": str(path.relative_to(ROOT)), "line": node.lineno, "finding": f"banned import {alias.name}"})
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in BANNED_IMPORTS:
                findings.append({"file": str(path.relative_to(ROOT)), "line": node.lineno, "finding": f"banned import {node.module}"})
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            findings.append({"file": str(path.relative_to(ROOT)), "line": node.lineno, "finding": f"banned call {node.func.id}"})
html = (SRC / "resources" / "valueark.html").read_text(encoding="utf-8")
for token in ["fetch(", "XMLHttpRequest", "WebSocket(", "EventSource(", "navigator.sendBeacon"]:
    if token in html:
        findings.append({"file": "resources/valueark.html", "finding": f"network-capable browser token: {token}"})
receipt = {
    "files_scanned": len(files),
    "findings": findings,
    "passed": not findings,
    "notice": "Static token/AST audit; not a substitute for independent security assessment."
}
out = ROOT / "validation" / "STATIC_AUDIT_RECEIPT.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
raise SystemExit(0 if receipt["passed"] else 1)
