"""Test configuration: isolate every run on a throwaway SQLite database."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Set BEFORE the app is imported so settings/engine bind to the test DB.
_TMP_DB = Path(tempfile.gettempdir()) / "aep-test.db"
_TMP_DB.unlink(missing_ok=True)
os.environ["AEP_ENV"] = "test"
os.environ["AEP_DATABASE_URL"] = f"sqlite+pysqlite:///{_TMP_DB.as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())
