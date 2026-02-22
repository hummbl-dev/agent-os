"""Shared pytest fixtures for cost-governor tests.

Provides:
- ROOT, SCHEMA_PATH, EXAMPLES_DIR constants
- load_json() helper
- schema_path, example_files session-scoped fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "openclaw.cost_governor.schema.json"
EXAMPLES_DIR = ROOT / "examples"


def load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def schema_path() -> Path:
    """Path to the cost_governor JSON Schema."""
    return SCHEMA_PATH


@pytest.fixture(scope="session")
def schema_data() -> dict:
    """Loaded cost_governor JSON Schema."""
    return load_json(SCHEMA_PATH)


@pytest.fixture(scope="session")
def example_files() -> list[Path]:
    """All example JSON files sorted by name."""
    return sorted(EXAMPLES_DIR.glob("*.json"))


@pytest.fixture(scope="session")
def tier_configs() -> dict[str, dict]:
    """All tier configs keyed by filename stem."""
    configs = {}
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        configs[path.stem] = load_json(path)
    return configs
