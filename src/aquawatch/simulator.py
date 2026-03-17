"""Generate realistic simulated water-quality sensor data."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import numpy as np

from aquawatch.models import SensorReading, SensorType, WaterSample


# Realistic parameter profiles for different water body types
PROFILES = {
    "clean_river": {
        "ph": (7.2, 0.3),
        "turbidity": (2.0, 1.5),
        "dissolved_oxygen": (9.0, 1.0),
        "temperature": (15.0, 3.0),
        "conductivity": (250.0, 50.0),
    },
    "urban_stream": {
        "ph": (7.5, 0.5),
        "turbidity": (15.0, 8.0),
        "dissolved_oxygen": (6.5, 1.5),
        "temperature": (20.0, 4.0),
        "conductivity": (600.0, 150.0),
    },
    "polluted_lake": {
        "ph": (6.0, 0.8),
        "turbidity": (50.0, 25.0),
        "dissolved_oxygen": (3.5, 1.2),
        "temperature": (22.0, 3.0),
        "conductivity": (1200.0, 300.0),
    },
    "drinking_water": {
        "ph": (7.0, 0.2),
        "turbidity": (0.3, 0.2),
        "dissolved_oxygen": (8.0, 0.5),
        "temperature": (18.0, 2.0),
        "conductivity": (350.0, 80.0),
    },
}

_UNITS = {
    "ph": "pH",
    "turbidity": "NTU",
    "dissolved_oxygen": "mg/L",
    "temperature": "C",
    "conductivity": "uS/cm",
}

_SENSOR_TYPE_MAP = {
    "ph": SensorType.PH,
    "turbidity": SensorType.TURBIDITY,
    "dissolved_oxygen": SensorType.DISSOLVED_OXYGEN,
    "temperature": SensorType.TEMPERATURE,
    "conductivity": SensorType.CONDUCTIVITY,
}


def generate_reading(
    parameter: str,
    mean: float,
    std: float,
    *,
    rng: np.random.Generator | None = None,
    location: str = "sim",
) -> SensorReading:
    """Generate a single sensor reading from a normal distribution."""
    if rng is None:
        rng = np.random.default_rng()
    value = float(rng.normal(mean, std))
    # Clamp non-negative parameters
    if parameter in ("turbidity", "dissolved_oxygen", "conductivity"):
        value = max(0.0, value)
    if parameter == "ph":
        value = max(0.0, min(14.0, value))
    return SensorReading(
        sensor_type=_SENSOR_TYPE_MAP[parameter],
        value=round(value, 2),
        unit=_UNITS[parameter],
        location=location,
        is_valid=True,
    )


def generate_sample(
    profile: str = "clean_river",
    *,
    location: str = "sim",
    timestamp: datetime | None = None,
    rng: np.random.Generator | None = None,
) -> WaterSample:
    """Generate a complete WaterSample using the given profile."""
    if rng is None:
        rng = np.random.default_rng()
    params = PROFILES[profile]
    readings = []
    for param, (mean, std) in params.items():
        r = generate_reading(param, mean, std, rng=rng, location=location)
        if timestamp:
            r.timestamp = timestamp
        readings.append(r)
    return WaterSample(
        sample_id=str(uuid.uuid4())[:8],
        timestamp=timestamp or datetime.now(),
        location=location,
        readings=readings,
    )


def generate_time_series(
    profile: str = "clean_river",
    n_samples: int = 24,
    interval_minutes: int = 60,
    *,
    location: str = "sim",
    trend: dict[str, float] | None = None,
    seed: int | None = None,
) -> list[WaterSample]:
    """Generate a time series of water samples.

    Parameters
    ----------
    profile:
        One of ``PROFILES`` keys.
    n_samples:
        Number of samples to generate.
    interval_minutes:
        Time between successive samples.
    trend:
        Optional dict mapping parameter names to a per-step additive drift.
        E.g. ``{"ph": -0.01}`` for slowly decreasing pH.
    seed:
        Random seed for reproducibility.
    """
    rng = np.random.default_rng(seed)
    params = dict(PROFILES[profile])
    base_time = datetime.now() - timedelta(minutes=interval_minutes * n_samples)
    samples = []
    for i in range(n_samples):
        ts = base_time + timedelta(minutes=interval_minutes * i)
        # Apply trend drift
        adjusted = {}
        for param, (mean, std) in params.items():
            drift = 0.0
            if trend and param in trend:
                drift = trend[param] * i
            adjusted[param] = (mean + drift, std)

        readings = []
        for param, (mean, std) in adjusted.items():
            readings.append(
                generate_reading(param, mean, std, rng=rng, location=location)
            )
            readings[-1].timestamp = ts
        samples.append(
            WaterSample(
                sample_id=f"ts-{i:04d}",
                timestamp=ts,
                location=location,
                readings=readings,
            )
        )
    return samples
