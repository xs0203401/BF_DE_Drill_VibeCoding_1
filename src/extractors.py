"""Input extractors for CSV and JSON source files."""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Extractor(ABC):
    """Common interface for reading source records."""

    @abstractmethod
    def extract(self, path: Path) -> list[dict[str, Any]]:
        """Read records from ``path`` and return them as dictionaries."""


class CSVExtractor(Extractor):
    """Extract dictionary records from a CSV file."""

    def extract(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8", newline="") as source:
            return list(csv.DictReader(source))


class JSONExtractor(Extractor):
    """Extract a list of dictionary records from a JSON file."""

    def extract(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as source:
            records = json.load(source)

        if not isinstance(records, list) or not all(
            isinstance(record, dict) for record in records
        ):
            raise ValueError(f"Expected a JSON list of objects: {path}")

        return records
