"""Shared pytest fixtures for logging contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "openclaw.log_event.schema.json"
EXAMPLES_DIR = ROOT / "examples"


def load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def schema_path() -> Path:
    return SCHEMA_PATH


@pytest.fixture(scope="session")
def example_files_valid() -> list[Path]:
    invalid = EXAMPLES_DIR / "example-invalid-missing-required.json"
    return sorted(path for path in EXAMPLES_DIR.glob("*.json") if path != invalid)


@pytest.fixture(scope="session")
def invalid_example_path() -> Path:
    return EXAMPLES_DIR / "example-invalid-missing-required.json"
