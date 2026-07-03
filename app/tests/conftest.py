import json
from pathlib import Path

import pytest


def pytest_configure() -> None:
    catalog_dest = Path("data/shl_assessments.json")
    catalog_dest.parent.mkdir(parents=True, exist_ok=True)
    if not catalog_dest.exists():
        catalog_dest.write_text(json.dumps([]), encoding="utf-8")
