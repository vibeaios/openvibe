"""Tests for platform_benchmarks.yaml shared memory file."""
import pathlib
import yaml

_BENCHMARKS_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "shared_memory" / "performance" / "platform_benchmarks.yaml"
)


def _load():
    return yaml.safe_load(_BENCHMARKS_PATH.read_text())


def test_platform_benchmarks_exists():
    assert _BENCHMARKS_PATH.exists()


def test_has_meta_benchmarks():
    data = _load()
    assert "meta" in data
    assert data["meta"]["bot_target_cpa"] == 400
    assert data["meta"]["dot_target_cpa"] == 300


def test_has_google_benchmarks():
    data = _load()
    assert "google" in data
    assert data["google"]["bot_target_cpa"] == 300


def test_has_amazon_benchmarks():
    data = _load()
    assert "amazon" in data
    assert data["amazon"]["bot_target_acos"] == 0.20


def test_has_tiktok_benchmarks():
    data = _load()
    assert "tiktok" in data
    assert data["tiktok"]["bot_target_cpa"] == 500


def test_has_linkedin_benchmarks():
    data = _load()
    assert "linkedin" in data
    assert data["linkedin"]["target_cpl"] == 150


def test_has_pinterest_benchmarks():
    data = _load()
    assert "pinterest" in data
    assert data["pinterest"]["bot_target_cpa"] == 350


def test_has_cross_platform_allocation():
    data = _load()
    assert "cross_platform" in data
    split = data["cross_platform"]["budget_split"]
    assert "google" in split
    assert "meta" in split
    assert "amazon" in split
