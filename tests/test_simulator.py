"""Tests for the simulator module."""

from aquawatch.simulator import (
    generate_reading,
    generate_sample,
    generate_time_series,
    PROFILES,
)
from aquawatch.models import SensorType


def test_generate_reading():
    r = generate_reading("ph", 7.0, 0.3)
    assert r.sensor_type == SensorType.PH
    assert r.unit == "pH"
    assert 0.0 <= r.value <= 14.0


def test_generate_sample_default():
    s = generate_sample()
    assert len(s.readings) == 5
    types = {r.sensor_type for r in s.readings}
    assert SensorType.PH in types
    assert SensorType.TURBIDITY in types
    assert SensorType.DISSOLVED_OXYGEN in types
    assert SensorType.TEMPERATURE in types
    assert SensorType.CONDUCTIVITY in types


def test_generate_sample_all_profiles():
    for profile in PROFILES:
        s = generate_sample(profile)
        assert len(s.readings) == 5


def test_generate_time_series():
    series = generate_time_series("clean_river", n_samples=10, seed=123)
    assert len(series) == 10
    # Timestamps should be increasing
    for i in range(1, len(series)):
        assert series[i].timestamp > series[i - 1].timestamp


def test_generate_time_series_with_trend():
    series = generate_time_series(
        "clean_river",
        n_samples=20,
        trend={"ph": -0.05},
        seed=42,
    )
    assert len(series) == 20


def test_reproducibility():
    s1 = generate_time_series("clean_river", n_samples=5, seed=99)
    s2 = generate_time_series("clean_river", n_samples=5, seed=99)
    for a, b in zip(s1, s2):
        for ra, rb in zip(a.readings, b.readings):
            assert ra.value == rb.value
