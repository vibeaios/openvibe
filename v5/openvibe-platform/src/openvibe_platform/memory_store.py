"""FileMemoryStore — filesystem-backed memory (debuggable with shell tools)."""

from __future__ import annotations

from pathlib import Path


class FileMemoryStore:
    """Filesystem-backed memory store. Layout: base_dir/{workspace}/{role_id}/"""

    def __init__(self, base_dir: Path | str) -> None:
        self._base = Path(base_dir)

    def _path(self, workspace: str, role_id: str, virtual_path: str) -> Path:
        return self._base / workspace / role_id / virtual_path.lstrip("/")

    def write(self, workspace: str, role_id: str,
              virtual_path: str, content: str) -> None:
        p = self._path(workspace, role_id, virtual_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def read(self, workspace: str, role_id: str,
             virtual_path: str) -> str | None:
        p = self._path(workspace, role_id, virtual_path)
        if not p.exists():
            return None
        return p.read_text(encoding="utf-8")

    def ls(self, workspace: str, role_id: str,
           virtual_path: str) -> list[str]:
        p = self._path(workspace, role_id, virtual_path)
        if not p.exists():
            return []
        return [entry.name for entry in sorted(p.iterdir())]

    def delete(self, workspace: str, role_id: str,
               virtual_path: str) -> None:
        p = self._path(workspace, role_id, virtual_path)
        if p.exists():
            p.unlink()

    def search(self, workspace: str, role_id: str,
               query: str) -> list[str]:
        """Simple substring search across all markdown files for this role."""
        base = self._base / workspace / role_id
        if not base.exists():
            return []
        results = []
        for f in base.rglob("*.md"):
            if query.lower() in f.read_text(encoding="utf-8").lower():
                results.append(str(f.relative_to(base)))
        return results
