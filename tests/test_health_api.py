"""Tests for Health Bridge API endpoints."""


class TestHealthCheck:
    def test_healthcheck_no_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthentication:
    def test_missing_api_key_returns_401(self, client):
        resp = client.get("/health/latest")
        assert resp.status_code == 401

    def test_invalid_api_key_returns_401(self, client):
        resp = client.get("/health/latest", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_valid_api_key_returns_200(self, client, auth_headers):
        resp = client.get("/health/latest", headers=auth_headers)
        assert resp.status_code == 200


class TestReceiveHealthData:
    def test_post_metrics(self, client, auth_headers, sample_metrics_payload):
        resp = client.post("/health/data", json=sample_metrics_payload, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "received"
        assert body["items_processed"] >= 1

    def test_post_workout(self, client, auth_headers, sample_workout_payload):
        resp = client.post("/health/data", json=sample_workout_payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["items_processed"] >= 1

    def test_post_raw_data(self, client, auth_headers):
        payload = {"data": {"heartRate": 75, "stepCount": 9000}}
        resp = client.post("/health/data", json=payload, headers=auth_headers)
        assert resp.status_code == 200

    def test_empty_payload_returns_400(self, client, auth_headers):
        resp = client.post("/health/data", json={}, headers=auth_headers)
        assert resp.status_code == 400


class TestGetLatestMetrics:
    def test_no_data_returns_message(self, client, auth_headers):
        resp = client.get("/health/latest", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    def test_with_data(self, client, auth_headers, seed_metrics):
        resp = client.get("/health/latest", headers=auth_headers)
        body = resp.json()
        assert body["latest"] is not None
        assert body["latest"]["heart_rate"] == 72.0


class TestGetHeartRate:
    def test_no_data(self, client, auth_headers):
        resp = client.get("/health/heart-rate", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["current"] == 0

    def test_with_data(self, client, auth_headers, seed_metrics):
        resp = client.get("/health/heart-rate", headers=auth_headers)
        body = resp.json()
        assert body["current"] == 72.0
        assert body["resting"] == 58.0
        assert len(body["readings"]) >= 1


class TestGetWaterIntake:
    def test_no_data(self, client, auth_headers):
        resp = client.get("/health/water", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["glasses"] == 0

    def test_with_data(self, client, auth_headers, seed_metrics):
        resp = client.get("/health/water", headers=auth_headers)
        assert resp.json()["glasses"] == 2.0


class TestGetWorkouts:
    def test_no_workouts(self, client, auth_headers):
        resp = client.get("/health/workouts", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_with_workout(self, client, auth_headers, sample_workout_payload):
        client.post("/health/data", json=sample_workout_payload, headers=auth_headers)
        resp = client.get("/health/workouts", headers=auth_headers)
        assert resp.json()["count"] >= 1


class TestGetDailySummary:
    def test_empty_summary(self, client, auth_headers):
        resp = client.get("/health/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data_points"] == 0

    def test_with_data(self, client, auth_headers, seed_metrics):
        resp = client.get("/health/summary", headers=auth_headers)
        body = resp.json()
        assert body["data_points"] >= 1


class TestGetRangeData:
    def test_valid_range(self, client, auth_headers):
        resp = client.get(
            "/health/range",
            params={"start": "2025-01-01", "end": "2025-01-07"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_invalid_date_format(self, client, auth_headers):
        resp = client.get(
            "/health/range",
            params={"start": "not-a-date"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_range_exceeds_90_days(self, client, auth_headers):
        resp = client.get(
            "/health/range",
            params={"start": "2025-01-01", "end": "2025-06-01"},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestAddWater:
    def test_add_default_glass(self, client, auth_headers):
        resp = client.post("/health/water/add", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["added"] == 1
        assert body["target"] == 8

    def test_add_custom_glasses(self, client, auth_headers):
        resp = client.post("/health/water/add?glasses=2.5", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["added"] == 2.5

    def test_glasses_below_minimum(self, client, auth_headers):
        resp = client.post("/health/water/add?glasses=0.1", headers=auth_headers)
        assert resp.status_code == 422

    def test_glasses_above_maximum(self, client, auth_headers):
        resp = client.post("/health/water/add?glasses=10", headers=auth_headers)
        assert resp.status_code == 422
