import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set env vars BEFORE any test module imports app.py (which reads them at module level)
TEST_API_KEY = "test-key-12345"
_test_data_dir = tempfile.mkdtemp()
os.environ.setdefault("API_KEY", TEST_API_KEY)
os.environ["DATA_DIR"] = _test_data_dir

# Ensure health-bridge module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "health-bridge"))


@pytest.fixture(autouse=True)
def _clean_data_dir(tmp_path, monkeypatch):
    """Point DATA_DIR to a fresh tmp_path for each test."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # Force reimport so app picks up new DATA_DIR
    if "app" in sys.modules:
        del sys.modules["app"]


@pytest.fixture()
def client(_clean_data_dir):
    """Create a fresh FastAPI TestClient."""
    from app import app as fastapi_app

    return TestClient(fastapi_app)


@pytest.fixture()
def auth_headers():
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture()
def sample_metrics_payload():
    return {
        "metrics": {
            "heart_rate": 72.0,
            "resting_hr": 58.0,
            "hrv": 45.0,
            "steps": 8500,
            "blood_oxygen": 98.5,
            "water_glasses": 2.0,
        }
    }


@pytest.fixture()
def sample_workout_payload():
    return {
        "workout": {
            "workout_type": "Running",
            "duration_min": 35.0,
            "distance_km": 5.2,
            "calories": 320.0,
            "avg_hr": 145.0,
        }
    }


@pytest.fixture()
def seed_metrics(client, auth_headers, sample_metrics_payload):
    """Post sample metrics so GET endpoints have data."""
    client.post("/health/data", json=sample_metrics_payload, headers=auth_headers)
