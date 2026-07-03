import json
from pathlib import Path
from typing import Iterator

from app.core.config import settings
from app.models.catalog import CatalogEntry, CatalogSchema


class CatalogLoader:
    """Loads and validates the SHL assessment catalog JSON once at startup."""

    def __init__(self, catalog_path: Path | None = None) -> None:
        self._catalog: list[CatalogEntry] = self._load_catalog(catalog_path)

    def _load_catalog(self, catalog_path: Path | None = None) -> list[CatalogEntry]:
        path = Path(catalog_path if catalog_path is not None else settings.catalog_path)
        if not path.exists():
            raise FileNotFoundError(f"Catalog file not found at {path}")

        with path.open("r", encoding="utf-8") as catalog_file:
            raw_catalog = json.loads(catalog_file.read(), strict=False)

        validated = CatalogSchema.model_validate(raw_catalog)
        return validated.root

    @property
    def catalog(self) -> list[CatalogEntry]:
        return self._catalog

    def iter_entries(self) -> Iterator[CatalogEntry]:
        yield from self._catalog


_catalog_loader_instance: CatalogLoader | None = None


def get_catalog_loader() -> CatalogLoader:
    """Lazy singleton getter for the CatalogLoader."""
    global _catalog_loader_instance
    if _catalog_loader_instance is None:
        _catalog_loader_instance = CatalogLoader()
    return _catalog_loader_instance
