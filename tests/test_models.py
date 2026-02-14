"""Tests for Pydantic data models and validation boundaries."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "health-bridge"))

# Import after path setup
from app import HealthMetric, WorkoutData  # noqa: E402


class TestHealthMetricValidation:
    def test_valid_metric(self):
        m = HealthMetric(heart_rate=72.0, steps=8500, blood_oxygen=98.0)
        assert m.heart_rate == 72.0
        assert m.steps == 8500

    def test_all_fields_optional(self):
        m = HealthMetric()
        assert m.heart_rate is None
        assert m.steps is None

    # Heart rate boundaries
    def test_heart_rate_lower_bound(self):
        m = HealthMetric(heart_rate=20)
        assert m.heart_rate == 20

    def test_heart_rate_upper_bound(self):
        m = HealthMetric(heart_rate=300)
        assert m.heart_rate == 300

    def test_heart_rate_below_minimum(self):
        with pytest.raises(ValidationError):
            HealthMetric(heart_rate=19)

    def test_heart_rate_above_maximum(self):
        with pytest.raises(ValidationError):
            HealthMetric(heart_rate=301)

    # Resting HR uses same validator
    def test_resting_hr_valid(self):
        m = HealthMetric(resting_hr=55.0)
        assert m.resting_hr == 55.0

    def test_resting_hr_below_minimum(self):
        with pytest.raises(ValidationError):
            HealthMetric(resting_hr=10)

    # Blood oxygen boundaries
    def test_blood_oxygen_lower_bound(self):
        m = HealthMetric(blood_oxygen=50)
        assert m.blood_oxygen == 50

    def test_blood_oxygen_upper_bound(self):
        m = HealthMetric(blood_oxygen=100)
        assert m.blood_oxygen == 100

    def test_blood_oxygen_below_minimum(self):
        with pytest.raises(ValidationError):
            HealthMetric(blood_oxygen=49)

    def test_blood_oxygen_above_maximum(self):
        with pytest.raises(ValidationError):
            HealthMetric(blood_oxygen=101)

    # Steps boundaries
    def test_steps_zero(self):
        m = HealthMetric(steps=0)
        assert m.steps == 0

    def test_steps_max(self):
        m = HealthMetric(steps=200000)
        assert m.steps == 200000

    def test_steps_negative(self):
        with pytest.raises(ValidationError):
            HealthMetric(steps=-1)

    def test_steps_above_maximum(self):
        with pytest.raises(ValidationError):
            HealthMetric(steps=200001)


class TestWorkoutDataValidation:
    def test_valid_workout(self):
        w = WorkoutData(workout_type="Running", duration_min=30.0, calories=250.0)
        assert w.workout_type == "Running"
        assert w.duration_min == 30.0

    def test_all_fields_optional(self):
        w = WorkoutData()
        assert w.duration_min is None

    # Duration boundaries
    def test_duration_zero(self):
        w = WorkoutData(duration_min=0)
        assert w.duration_min == 0

    def test_duration_max(self):
        w = WorkoutData(duration_min=1440)
        assert w.duration_min == 1440

    def test_duration_negative(self):
        with pytest.raises(ValidationError):
            WorkoutData(duration_min=-1)

    def test_duration_above_maximum(self):
        with pytest.raises(ValidationError):
            WorkoutData(duration_min=1441)
