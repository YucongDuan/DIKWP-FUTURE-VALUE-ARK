from __future__ import annotations

import json
from importlib import resources
from typing import Any


def load_defaults() -> dict[str, Any]:
    text = resources.files("dikwp_valueark.resources").joinpath("defaults.json").read_text(encoding="utf-8")
    return json.loads(text)
