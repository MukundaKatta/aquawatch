"""Water temperature sensor monitor."""

from __future__ import annotations

from aquawatch.models import SensorReading, SensorType


class TemperatureMonitor:
    """Water temperature sensor.

    EPA warm-water aquatic-life criterion: <= 30 C.
    WHO aesthetic guideline for drinking water: <= 25 C.
    """

    VALID_RANGE = (0.0, 50.0)  # Celsius
    EPA_MAX_WARMWATER = 30.0
    WHO_MAX_DRINKING = 25.0

    def __init__(self, sensor_id: str = "TEMP-001") -> None:
        self.sensor_id = sensor_id

    def read(self, value_c: float, location: str = "default") -> SensorReading:
        is_valid = self.VALID_RANGE[0] <= value_c <= self.VALID_RANGE[1]
        return SensorReading(
            sensor_type=SensorType.TEMPERATURE,
            value=round(value_c, 2),
            unit="C",
            location=location,
            is_valid=is_valid,
            error_margin=0.5,
        )

    def check_epa_warmwater(self, value: float) -> bool:
        return value <= self.EPA_MAX_WARMWATER

    def check_who_drinking(self, value: float) -> bool:
        return value <= self.WHO_MAX_DRINKING
