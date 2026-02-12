"""
Mitra Health Bridge - Apple Health Data Receiver & API

Receives health data from iPhone via:
  - Health Auto Export app (REST API)
  - Apple Shortcuts (webhook)

Provides REST API for N8N workflows to query health metrics.
"""

import json
import logging
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# ─── Logging Setup ──────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("health-bridge")

# ─── App Setup ──────────────────────────────────────────────

app = FastAPI(
    title="Mitra Health Bridge",
    version="1.0.0",
    docs_url=None,  # Disable Swagger in production
    redoc_url=None,
)

# CORS - allow Health Auto Export app and local N8N
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5678",
        "http://mitra-n8n:5678",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.error("API_KEY environment variable is required")
    sys.exit(1)

MAX_REQUEST_SIZE = 1 * 1024 * 1024  # 1MB max payload


# ─── Authentication ─────────────────────────────────────────


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Validate API key on all protected endpoints."""
    if not x_api_key or x_api_key != API_KEY:
        logger.warning("Unauthorized request - invalid or missing API key")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


# ─── Request Size Limiter ───────────────────────────────────


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            raise HTTPException(status_code=413, detail="Request too large")
    return await call_next(request)


# ─── Data Models ────────────────────────────────────────────


class HealthMetric(BaseModel):
    timestamp: Optional[str] = None
    heart_rate: Optional[float] = None
    resting_hr: Optional[float] = None
    hrv: Optional[float] = None
    steps: Optional[int] = None
    active_calories: Optional[float] = None
    water_ml: Optional[float] = None
    water_glasses: Optional[float] = None
    sleep_hours: Optional[float] = None
    blood_oxygen: Optional[float] = None
    distance_km: Optional[float] = None
    flights_climbed: Optional[int] = None
    standing_hours: Optional[int] = None
    respiratory_rate: Optional[float] = None
    body_temperature: Optional[float] = None
    weight_kg: Optional[float] = None

    @field_validator("heart_rate", "resting_hr", mode="before")
    @classmethod
    def validate_heart_rate(cls, v):
        if v is not None and (v < 20 or v > 300):
            raise ValueError("Heart rate must be between 20-300 bpm")
        return v

    @field_validator("blood_oxygen", mode="before")
    @classmethod
    def validate_spo2(cls, v):
        if v is not None and (v < 50 or v > 100):
            raise ValueError("Blood oxygen must be between 50-100%")
        return v

    @field_validator("steps", mode="before")
    @classmethod
    def validate_steps(cls, v):
        if v is not None and (v < 0 or v > 200000):
            raise ValueError("Steps must be between 0-200000")
        return v


class WorkoutData(BaseModel):
    timestamp: Optional[str] = None
    workout_type: Optional[str] = None
    duration_min: Optional[float] = None
    distance_km: Optional[float] = None
    calories: Optional[float] = None
    avg_hr: Optional[float] = None
    max_hr: Optional[float] = None
    avg_pace: Optional[str] = None
    elevation_gain: Optional[float] = None

    @field_validator("duration_min", mode="before")
    @classmethod
    def validate_duration(cls, v):
        if v is not None and (v < 0 or v > 1440):
            raise ValueError("Duration must be between 0-1440 minutes")
        return v


class HealthExport(BaseModel):
    """Flexible health data payload from Health Auto Export or Shortcuts."""
    metrics: Optional[HealthMetric] = None
    workout: Optional[WorkoutData] = None
    data: Optional[dict] = None


# ─── Helpers ────────────────────────────────────────────────


def _today_str() -> str:
    return date.today().isoformat()


def _get_data_file(category: str, day: str = None) -> Path:
    day = day or _today_str()
    # Sanitize day input to prevent path traversal
    try:
        date.fromisoformat(day)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {day}")
    return DATA_DIR / f"{category}_{day}.json"


def _load_data(category: str, day: str = None) -> list[dict]:
    f = _get_data_file(category, day)
    if f.exists():
        try:
            return json.loads(f.read_text())
        except json.JSONDecodeError:
            logger.error(f"Corrupted data file: {f}")
            return []
    return []


def _save_data(category: str, data: list[dict], day: str = None):
    f = _get_data_file(category, day)
    f.write_text(json.dumps(data, indent=2, default=str))
    logger.debug(f"Saved {len(data)} entries to {f.name}")


# ─── Health Check (unauthenticated for Docker) ─────────────


@app.get("/health")
async def health_check():
    """Docker health check endpoint - no auth required."""
    return {"status": "ok", "service": "mitra-health-bridge"}


# ─── Receive Health Data ────────────────────────────────────


@app.post("/health/data", dependencies=[Depends(verify_api_key)])
async def receive_health_data(payload: HealthExport):
    """Receive health data from Health Auto Export app or Apple Shortcuts."""
    now = datetime.now().isoformat()
    received_count = 0

    if payload.metrics:
        metrics_data = _load_data("metrics")
        entry = payload.metrics.model_dump(exclude_none=True)
        entry["received_at"] = now
        if "timestamp" not in entry:
            entry["timestamp"] = now
        metrics_data.append(entry)
        _save_data("metrics", metrics_data)
        received_count += 1
        logger.info(f"Received health metrics: {list(entry.keys())}")

    if payload.workout:
        workout_data = _load_data("workouts")
        entry = payload.workout.model_dump(exclude_none=True)
        entry["received_at"] = now
        if "timestamp" not in entry:
            entry["timestamp"] = now
        workout_data.append(entry)
        _save_data("workouts", workout_data)
        received_count += 1
        logger.info(f"Received workout: {entry.get('workout_type', 'unknown')}")

    if payload.data:
        raw_data = _load_data("raw")
        payload.data["received_at"] = now
        raw_data.append(payload.data)
        _save_data("raw", raw_data)

        metrics_data = _load_data("metrics")
        extracted = _extract_from_raw(payload.data)
        if extracted:
            extracted["received_at"] = now
            extracted["timestamp"] = now
            metrics_data.append(extracted)
            _save_data("metrics", metrics_data)
            received_count += 1
            logger.info(f"Extracted metrics from raw data: {list(extracted.keys())}")

    if received_count == 0 and not payload.data:
        raise HTTPException(status_code=400, detail="No valid health data in payload")

    return {"status": "received", "timestamp": now, "items_processed": received_count}


def _extract_from_raw(data: dict) -> dict | None:
    """Extract standard metrics from Health Auto Export format."""
    extracted = {}

    mappings = {
        "heart_rate": ["heartRate", "heart_rate", "HeartRate", "bpm"],
        "resting_hr": ["restingHeartRate", "resting_hr", "RestingHeartRate"],
        "hrv": ["heartRateVariability", "hrv", "HRV", "heartRateVariabilitySDNN"],
        "steps": ["stepCount", "steps", "StepCount"],
        "active_calories": ["activeEnergyBurned", "active_calories", "ActiveCalories"],
        "water_ml": ["dietaryWater", "water_ml", "water"],
        "sleep_hours": ["sleepAnalysis", "sleep_hours", "sleep"],
        "blood_oxygen": ["oxygenSaturation", "blood_oxygen", "SpO2", "spo2"],
        "distance_km": ["distanceWalkingRunning", "distance_km", "distance"],
        "weight_kg": ["bodyMass", "weight_kg", "weight"],
    }

    for standard_key, possible_keys in mappings.items():
        for pk in possible_keys:
            if pk in data:
                val = data[pk]
                if isinstance(val, dict):
                    val = val.get("qty") or val.get("value") or val.get("avg")
                if val is not None:
                    try:
                        extracted[standard_key] = float(val)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {pk}={val} to float")
                    break

    if "water_ml" in extracted and "water_glasses" not in extracted:
        extracted["water_glasses"] = round(extracted["water_ml"] / 250, 1)

    return extracted if extracted else None


# ─── Query Endpoints (all authenticated) ────────────────────


@app.get("/health/latest", dependencies=[Depends(verify_api_key)])
async def get_latest_metrics():
    """Get the most recent health metrics."""
    metrics = _load_data("metrics")
    if not metrics:
        return {"message": "No health data available yet", "data": None}

    latest = metrics[-1]
    today_metrics = _load_data("metrics", _today_str())
    aggregated = _aggregate_daily(today_metrics)

    return {
        "latest": latest,
        "today_summary": aggregated,
        "data_points_today": len(today_metrics),
    }


@app.get("/health/heart-rate", dependencies=[Depends(verify_api_key)])
async def get_heart_rate():
    """Get heart rate data for today."""
    metrics = _load_data("metrics")
    hr_data = [m for m in metrics if m.get("heart_rate")]

    if not hr_data:
        return {"current": 0, "resting": 0, "readings": [], "message": "No heart rate data"}

    latest = hr_data[-1]
    readings = [{"time": m.get("timestamp", ""), "hr": m["heart_rate"]} for m in hr_data[-20:]]
    hrs = [m["heart_rate"] for m in hr_data]

    return {
        "current": latest.get("heart_rate", 0),
        "resting": latest.get("resting_hr", 0),
        "hrv": latest.get("hrv", 0),
        "min": min(hrs) if hrs else 0,
        "max": max(hrs) if hrs else 0,
        "avg": round(sum(hrs) / len(hrs), 1) if hrs else 0,
        "readings": readings,
    }


@app.get("/health/water", dependencies=[Depends(verify_api_key)])
async def get_water_intake():
    """Get today's water intake."""
    metrics = _load_data("metrics")
    water_entries = [m for m in metrics if m.get("water_glasses") or m.get("water_ml")]

    total_glasses = sum(m.get("water_glasses", 0) for m in water_entries)
    total_ml = sum(m.get("water_ml", 0) for m in water_entries)

    if total_ml > 0 and total_glasses == 0:
        total_glasses = round(total_ml / 250, 1)

    return {
        "glasses": total_glasses,
        "ml": total_ml,
        "target_glasses": 8,
        "target_ml": 3000,
        "percentage": round(total_glasses / 8 * 100, 1) if total_glasses else 0,
    }


@app.get("/health/workouts", dependencies=[Depends(verify_api_key)])
async def get_workouts(days: int = Query(default=7, ge=1, le=90)):
    """Get recent workouts."""
    all_workouts = []

    for i in range(days):
        day = (date.today() - timedelta(days=i)).isoformat()
        day_workouts = _load_data("workouts", day)
        all_workouts.extend(day_workouts)

    return {
        "workouts": all_workouts[:100],  # Cap response size
        "count": len(all_workouts),
        "days_queried": days,
    }


@app.get("/health/summary", dependencies=[Depends(verify_api_key)])
async def get_daily_summary():
    """Get comprehensive daily health summary."""
    metrics = _load_data("metrics")
    workouts = _load_data("workouts")
    aggregated = _aggregate_daily(metrics)

    return {
        "date": _today_str(),
        "metrics": aggregated,
        "workouts": workouts,
        "workout_count": len(workouts),
        "data_points": len(metrics),
    }


@app.get("/health/range", dependencies=[Depends(verify_api_key)])
async def get_range_data(
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get health data for a date range."""
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end) if end else date.today()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    if (end_date - start_date).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")

    all_metrics = []
    all_workouts = []
    current = start_date

    while current <= end_date:
        day_str = current.isoformat()
        all_metrics.extend(_load_data("metrics", day_str))
        all_workouts.extend(_load_data("workouts", day_str))
        current += timedelta(days=1)

    return {
        "start": start,
        "end": end_date.isoformat(),
        "metrics": all_metrics[-500:],  # Cap response size
        "workouts": all_workouts[-100:],
        "total_metrics": len(all_metrics),
        "total_workouts": len(all_workouts),
    }


@app.post("/health/water/add", dependencies=[Depends(verify_api_key)])
async def add_water(glasses: float = Query(default=1, ge=0.5, le=5)):
    """Manually log water intake."""
    metrics = _load_data("metrics")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "water_glasses": glasses,
        "water_ml": glasses * 250,
        "received_at": datetime.now().isoformat(),
    }
    metrics.append(entry)
    _save_data("metrics", metrics)

    total = sum(m.get("water_glasses", 0) for m in metrics)
    logger.info(f"Water logged: +{glasses} glasses, total today: {total}")
    return {"added": glasses, "total_today": total, "target": 8}


# ─── Aggregation Helper ────────────────────────────────────


def _aggregate_daily(metrics: list[dict]) -> dict:
    """Aggregate a day's metrics into a summary."""
    if not metrics:
        return {
            "heart_rate_avg": 0, "resting_hr": 0, "hrv_avg": 0,
            "steps": 0, "active_calories": 0, "water_glasses": 0,
            "sleep_hours": 0, "blood_oxygen_avg": 0,
        }

    def _avg(key):
        vals = [m[key] for m in metrics if m.get(key)]
        return round(sum(vals) / len(vals), 1) if vals else 0

    def _max_val(key):
        vals = [m[key] for m in metrics if m.get(key)]
        return max(vals) if vals else 0

    def _sum_val(key):
        return sum(m.get(key, 0) for m in metrics)

    def _last(key):
        for m in reversed(metrics):
            if m.get(key):
                return m[key]
        return 0

    return {
        "heart_rate_avg": _avg("heart_rate"),
        "heart_rate_max": _max_val("heart_rate"),
        "resting_hr": _last("resting_hr"),
        "hrv_avg": _avg("hrv"),
        "steps": _max_val("steps"),
        "active_calories": _max_val("active_calories"),
        "water_glasses": _sum_val("water_glasses"),
        "sleep_hours": _last("sleep_hours"),
        "blood_oxygen_avg": _avg("blood_oxygen"),
        "distance_km": _max_val("distance_km"),
        "weight_kg": _last("weight_kg"),
    }
