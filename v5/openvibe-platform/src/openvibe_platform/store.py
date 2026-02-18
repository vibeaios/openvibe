"""JSONFileStore — simple file-backed persistence for platform services."""

from __future__ import annotations

import json
from pathlib import Path


class JSONFileStore:
    """Persist lists of dicts as JSON files under a base directory."""

    def __init__(self, data_dir: Path) -> None:
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def load(self, filename: str) -> list[dict]:
        """Return parsed JSON list, or [] if file does not exist."""
        path = self._dir / filename
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def save(self, filename: str, data: list[dict]) -> None:
        """Overwrite file with JSON-serialized data. Datetimes → ISO strings."""
        path = self._dir / filename
        path.write_text(json.dumps(data, default=str, indent=2))
