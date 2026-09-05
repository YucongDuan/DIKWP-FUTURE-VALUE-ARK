import json
from pathlib import Path

from dikwp_valueark.cli import main
from dikwp_valueark.defaults import load_defaults
from dikwp_valueark.optimizer import analyze_and_optimize
from dikwp_valueark.report import markdown_report


def test_cli_demo_creates_outputs(tmp_path: Path):
    rc = main(["demo", "--workspace", str(tmp_path), "--reset"])
    assert rc == 0
    for name in ["analysis.json", "valueark-report.md", "valueark-report.html", "futurevalue-ark.html"]:
        assert (tmp_path / name).exists()
    data = json.loads((tmp_path / "analysis.json").read_text(encoding="utf-8"))
    assert data["status"] == "EDUCATIONAL_DECISION_SUPPORT_ONLY"


def test_report_uses_declared_scenario_language():
    d = load_defaults()
    p = {
        "name": "report test",
        "settings": {**d["default_settings"], "candidate_count": 1000},
        "holdings": {a["id"]: a["default_amount"] for a in d["assets"]},
        "scenario_weights": d["alert_presets"]["yellow"],
    }
    report = markdown_report(analyze_and_optimize(p, defaults=d))
    assert "声明情景财富底线（非保证）" in report
    assert "不是个性化证券推荐" in report
    assert "不用杠杆" in report
