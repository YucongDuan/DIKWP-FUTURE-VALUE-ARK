from __future__ import annotations

from importlib import resources
from pathlib import Path


def dashboard_text() -> str:
    return resources.files("dikwp_valueark.resources").joinpath("valueark.html").read_text(encoding="utf-8")


def export_dashboard(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dashboard_text(), encoding="utf-8")
    return target
