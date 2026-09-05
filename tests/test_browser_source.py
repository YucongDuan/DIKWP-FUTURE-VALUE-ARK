import re
from pathlib import Path


def test_embedded_javascript_is_present_and_no_remote_assets():
    path = Path(__file__).resolve().parents[1] / "DIKWP_FUTURE_VALUE_ARK_v1.0.0.html"
    text = path.read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", text, re.S)
    assert len(scripts) == 1
    assert "function analyze(" in scripts[0]
    assert "function renderResults(" in scripts[0]
    assert "src=\"http" not in text
    assert "href=\"http" not in text
