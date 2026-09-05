from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "DIKWP_FUTURE_VALUE_ARK_v1.0.0.html"
OUT = ROOT / "validation" / "BROWSER_SMOKE_RECEIPT.json"
SCREENSHOT = ROOT / "validation" / "BROWSER_SMOKE_SCREENSHOT.png"

errors: list[str] = []
html = HTML.read_text(encoding="utf-8")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.on("pageerror", lambda e: errors.append("PAGE:" + str(e)))
    page.on("console", lambda m: errors.append("CONSOLE:" + m.text) if m.type == "error" else None)
    page.set_content(html, wait_until="load")
    page.locator("#candidate_count").fill("2500")
    page.locator("#runBtn").click()
    status = ""
    started = time.time()
    for _ in range(300):
        status = page.locator("#runStatus").inner_text()
        if "完成" in status or "错误" in status:
            break
        time.sleep(0.1)
    elapsed = time.time() - started
    receipt = {
        "title": page.title(),
        "asset_inputs": page.locator(".asset-input").count(),
        "scenario_inputs": page.locator(".weight-input").count(),
        "status": status,
        "kpi_cards": page.locator("#kpis .kpi").count(),
        "rebalance_rows": page.locator("#rebalanceBody tr").count(),
        "warning_rows": page.locator("#warnings .warning").count(),
        "elapsed_seconds": round(elapsed, 4),
        "page_errors": errors,
        "passed": "完成" in status and not errors,
        "notice": "Headless browser smoke test using page.set_content; not a full usability or security assessment."
    }
    page.screenshot(path=str(SCREENSHOT), full_page=True)
    browser.close()
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
raise SystemExit(0 if receipt["passed"] else 1)
