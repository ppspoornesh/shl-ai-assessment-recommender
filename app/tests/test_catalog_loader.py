import json
from pathlib import Path

from app.services.catalog_loader import CatalogLoader


def test_catalog_loader_validates_and_loads(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps([
        {
            "entity_id": "1",
            "name": "Leadership Assessment",
            "link": "https://example.com/leadership",
            "description": "Evaluates leadership potential.",
            "duration": "30 mins",
            "job_levels": ["Manager"],
            "keys": ["leadership", "team"],
        }
    ]), encoding="utf-8")

    loader = CatalogLoader(catalog_path=catalog_path)

    assert len(loader.catalog) == 1
    assert loader.catalog[0].entity_id == "1"
    assert loader.catalog[0].name == "Leadership Assessment"
