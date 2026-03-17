"""Electrical conductivity sensor monitor."""

from __future__ import annotations

from aquawatch.models import SensorReading, SensorType


class ConductivityMonitor:
    """Electrical conductivity (EC) sensor.

    EPA secondary standard for drinking water: <= 800 uS/cm.
    WHO guideline: <= 1000 uS/cm.
    Typical freshwater: 50-1500 uS/cm.
    """

    VALID_RANGE = (0.0, 100_000.0)  # uS/cm
    EPA_MAX = 800.0
    WHO_MAX = 1000.0

    def __init__(self, sensor_id: str = "EC-001") -> None:
        self.sensor_id = sensor_id

    def read(self, value_us_cm: float, location: str = "default") -> SensorReading:
        is_valid = self.VALID_RANGE[0] <= value_us_cm <= self.VALID_RANGE[1]
        return SensorReading(
            sensor_type=SensorType.CONDUCTIVITY,
            value=round(value_us_cm, 2),
            unit="uS/cm",
            location=location,
            is_valid=is_valid,
            error_margin=5.0,
        )

    def estimate_tds(self, conductivity_us_cm: float, factor: float = 0.65) -> float:
        """Estimate Total Dissolved Solids from conductivity.

        The conversion factor varies by water source (0.55-0.80).
        Default 0.65 is typical for mixed-mineral freshwater.
        """
        return round(conductivity_us_cm * factor, 2)

    def check_epa(self, value: float) -> bool:
        return value <= self.EPA_MAX

    def check_who(self, value: float) -> bool:
        return value <= self.WHO_MAX
