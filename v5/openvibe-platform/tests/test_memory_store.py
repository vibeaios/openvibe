from pathlib import Path
from openvibe_platform.memory_store import FileMemoryStore


def test_write_and_read_file(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "knowledge/sales/principles.md",
                "VP sponsor predicts conversion.")
    content = store.read("vibe-team", "cro", "knowledge/sales/principles.md")
    assert "VP sponsor" in content


def test_list_directory(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "knowledge/sales/a.md", "content a")
    store.write("vibe-team", "cro", "knowledge/sales/b.md", "content b")
    entries = store.ls("vibe-team", "cro", "knowledge/sales")
    assert "a.md" in entries
    assert "b.md" in entries


def test_file_not_found_returns_none(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    result = store.read("vibe-team", "cro", "knowledge/nothing.md")
    assert result is None


def test_delete_file(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "experience/2026-02/event.md", "stuff")
    store.delete("vibe-team", "cro", "experience/2026-02/event.md")
    assert store.read("vibe-team", "cro", "experience/2026-02/event.md") is None


def test_search_by_content(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "knowledge/sales/principles.md",
                "VP sponsor predicts conversion")
    store.write("vibe-team", "cro", "knowledge/product/roadmap.md",
                "Q3 features planned")
    results = store.search("vibe-team", "cro", "VP sponsor")
    assert len(results) == 1
    assert "principles.md" in results[0]
