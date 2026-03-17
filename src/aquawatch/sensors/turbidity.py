"""Turbidity sensor monitor."""

from __future__ import annotations

from aquawatch.models import SensorReading, SensorType


class TurbidityMonitor:
    """Nephelometric turbidity sensor.

    Thresholds based on EPA Surface Water Treatment Rule and WHO guidelines.
    - EPA MCL: <= 1 NTU (must be <= 0.3 NTU in 95 % of monthly samples)
    - WHO guideline: <= 4 NTU (ideally < 1 NTU)
    """

    VALID_RANGE = (0.0, 4000.0)  # NTU sensor range
    EPA_MAX = 1.0  # NTU
    WHO_MAX = 4.0  # NTU

    def __init__(self, sensor_id: str = "TURB-001") -> None:
        self.sensor_id = sensor_id

    def read(self, raw_ntu: float, location: str = "default") -> SensorReading:
        """Create a SensorReading from a turbidity measurement in NTU."""
        is_valid = self.VALID_RANGE[0] <= raw_ntu <= self.VALID_RANGE[1]
        return SensorReading(
            sensor_type=SensorType.TURBIDITY,
            value=round(raw_ntu, 2),
            unit="NTU",
            location=location,
            is_valid=is_valid,
            error_margin=0.05,
        )

    def check_epa(self, value: float) -> bool:
        """Return True if turbidity meets EPA standard."""
        return value <= self.EPA_MAX

    def check_who(self, value: float) -> bool:
        """Return True if turbidity meets WHO guideline."""
        return value <= self.WHO_MAX
