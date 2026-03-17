"""Dissolved oxygen sensor monitor."""

from __future__ import annotations

import numpy as np

from aquawatch.models import SensorReading, SensorType


class DOMonitor:
    """Dissolved oxygen sensor.

    Thresholds per EPA aquatic-life criteria:
    - >= 5 mg/L  optimal for most aquatic life
    - >= 4 mg/L  minimum for warm-water species
    - <  2 mg/L  hypoxic / dead-zone conditions
    """

    VALID_RANGE = (0.0, 20.0)  # mg/L
    OPTIMAL_MIN = 5.0
    EPA_MIN = 4.0
    HYPOXIC = 2.0

    def __init__(self, sensor_id: str = "DO-001") -> None:
        self.sensor_id = sensor_id

    def read(self, value_mg_l: float, location: str = "default") -> SensorReading:
        is_valid = self.VALID_RANGE[0] <= value_mg_l <= self.VALID_RANGE[1]
        return SensorReading(
            sensor_type=SensorType.DISSOLVED_OXYGEN,
            value=round(value_mg_l, 2),
            unit="mg/L",
            location=location,
            is_valid=is_valid,
            error_margin=0.1,
        )

    @staticmethod
    def saturation_concentration(temperature_c: float, salinity_ppt: float = 0.0) -> float:
        """Calculate DO saturation (mg/L) using the Benson-Krause equation.

        Simplified form for fresh/brackish water.
        """
        t = temperature_c
        # Empirical coefficients (valid 0-40 C, salinity 0-40 ppt)
        ln_do = (
            -139.34411
            + 1.575701e5 / (t + 273.15)
            - 6.642308e7 / (t + 273.15) ** 2
            + 1.243800e10 / (t + 273.15) ** 3
            - 8.621949e11 / (t + 273.15) ** 4
        )
        do_sat = float(np.exp(ln_do))
        # Salinity correction (simplified)
        do_sat *= 1.0 - 0.0001 * salinity_ppt
        return round(do_sat, 2)

    def check_healthy(self, value: float) -> bool:
        return value >= self.OPTIMAL_MIN

    def is_hypoxic(self, value: float) -> bool:
        return value < self.HYPOXIC
