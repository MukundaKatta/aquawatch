"""pH sensor monitor with multi-point calibration support."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np

from aquawatch.models import SensorReading, SensorType


class PHMonitor:
    """pH sensor with calibration curve support.

    Supports 1-point, 2-point, and 3-point calibration using standard
    buffer solutions (pH 4.01, 7.00, 10.01).
    """

    STANDARD_BUFFERS = {
        "acid": 4.01,
        "neutral": 7.00,
        "base": 10.01,
    }

    # EPA/WHO acceptable range for drinking water
    VALID_RANGE = (0.0, 14.0)
    ACCEPTABLE_RANGE = (6.5, 8.5)

    def __init__(self, sensor_id: str = "pH-001") -> None:
        self.sensor_id = sensor_id
        self._calibration_points: list[tuple[float, float]] = []  # (raw, actual)
        self._slope: float = 1.0
        self._offset: float = 0.0
        self._last_calibration: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def add_calibration_point(self, raw_value: float, buffer_ph: float) -> None:
        """Record a calibration point mapping raw ADC/mV reading to known pH."""
        self._calibration_points.append((raw_value, buffer_ph))
        if len(self._calibration_points) >= 2:
            self._fit_calibration()
        elif len(self._calibration_points) == 1:
            # Single-point offset calibration
            self._offset = buffer_ph - raw_value
            self._slope = 1.0
        self._last_calibration = datetime.now()

    def _fit_calibration(self) -> None:
        """Fit a linear calibration curve through stored points."""
        raws = np.array([p[0] for p in self._calibration_points])
        actuals = np.array([p[1] for p in self._calibration_points])
        coeffs = np.polyfit(raws, actuals, deg=1)
        self._slope = float(coeffs[0])
        self._offset = float(coeffs[1])

    def calibrate(
        self,
        raw_values: dict[str, float],
    ) -> None:
        """Convenience method: calibrate with named buffer solutions.

        Parameters
        ----------
        raw_values:
            Mapping of buffer name (``"acid"``, ``"neutral"``, ``"base"``)
            to the raw sensor reading in that solution.
        """
        self._calibration_points.clear()
        for name, raw in raw_values.items():
            buffer_ph = self.STANDARD_BUFFERS.get(name)
            if buffer_ph is None:
                raise ValueError(
                    f"Unknown buffer '{name}'. Use: {list(self.STANDARD_BUFFERS)}"
                )
            self.add_calibration_point(raw, buffer_ph)

    @property
    def is_calibrated(self) -> bool:
        return len(self._calibration_points) >= 2

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def apply_calibration(self, raw_value: float) -> float:
        """Convert a raw sensor value to calibrated pH."""
        return self._slope * raw_value + self._offset

    def read(self, raw_value: float, location: str = "default") -> SensorReading:
        """Produce a calibrated SensorReading from a raw value."""
        calibrated = self.apply_calibration(raw_value)
        is_valid = self.VALID_RANGE[0] <= calibrated <= self.VALID_RANGE[1]
        return SensorReading(
            sensor_type=SensorType.PH,
            value=round(calibrated, 2),
            unit="pH",
            location=location,
            is_valid=is_valid,
            error_margin=0.02 if self.is_calibrated else 0.1,
        )

    def check_acceptable(self, value: float) -> bool:
        """Return True if pH falls within EPA/WHO drinking-water range."""
        return self.ACCEPTABLE_RANGE[0] <= value <= self.ACCEPTABLE_RANGE[1]
