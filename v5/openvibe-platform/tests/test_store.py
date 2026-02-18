"""Tests for JSONFileStore."""
import pytest
from openvibe_platform.store import JSONFileStore


def test_load_missing_file(tmp_path):
    store = JSONFileStore(tmp_path)
    assert store.load("nonexistent.json") == []


def test_save_and_load(tmp_path):
    store = JSONFileStore(tmp_path)
    store.save("items.json", [{"id": "a", "name": "Alpha"}])
    assert store.load("items.json") == [{"id": "a", "name": "Alpha"}]


def test_save_creates_parent_dirs(tmp_path):
    store = JSONFileStore(tmp_path / "nested" / "dir")
    store.save("x.json", [])
    assert (tmp_path / "nested" / "dir" / "x.json").exists()


def test_save_overwrites(tmp_path):
    store = JSONFileStore(tmp_path)
    store.save("items.json", [{"id": "a"}])
    store.save("items.json", [{"id": "b"}])
    assert store.load("items.json") == [{"id": "b"}]


def test_datetime_serialized_as_string(tmp_path):
    from datetime import datetime, timezone
    store = JSONFileStore(tmp_path)
    store.save("items.json", [{"ts": datetime.now(timezone.utc)}])
    loaded = store.load("items.json")
    assert isinstance(loaded[0]["ts"], str)
