"""Contamination detection via statistical anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats as sp_stats

from aquawatch.models import (
    Alert,
    AlertSeverity,
    EPA_THRESHOLDS,
    SensorReading,
    WaterSample,
)


@dataclass
class ContaminationDetector:
    """Detect contamination events using threshold checks and anomaly detection.

    Two detection strategies:
    1. **Threshold-based** -- compare readings against EPA/WHO limits.
    2. **Statistical anomaly** -- maintain a sliding window of recent readings
       and flag values beyond ``z_threshold`` standard deviations from the mean
       (modified Z-score using median absolute deviation for robustness).
    """

    z_threshold: float = 3.0
    window_size: int = 50
    _history: dict[str, list[float]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # History management
    # ------------------------------------------------------------------

    def record(self, reading: SensorReading) -> None:
        """Add a reading to the sliding history window."""
        key = reading.sensor_type.value
        if key not in self._history:
            self._history[key] = []
        self._history[key].append(reading.value)
        # Trim to window
        if len(self._history[key]) > self.window_size:
            self._history[key] = self._history[key][-self.window_size :]

    def record_sample(self, sample: WaterSample) -> None:
        """Record all readings in a sample."""
        for reading in sample.readings:
            self.record(reading)

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def check_thresholds(self, sample: WaterSample) -> list[Alert]:
        """Check sample readings against EPA thresholds."""
        alerts: list[Alert] = []
        for reading in sample.readings:
            key = reading.sensor_type.value
            limits = EPA_THRESHOLDS.get(key)
            if limits is None:
                continue
            lo = limits.get("min")
            hi = limits.get("max")
            if lo is not None and reading.value < lo:
                alerts.append(
                    Alert(
                        severity=AlertSeverity.CRITICAL,
                        parameter=key,
                        message=f"{key} below EPA minimum ({lo} {limits['unit']})",
                        value=reading.value,
                        threshold=lo,
                    )
                )
            if hi is not None and reading.value > hi:
                sev = (
                    AlertSeverity.CRITICAL
                    if reading.value > hi * 1.5
                    else AlertSeverity.WARNING
                )
                alerts.append(
                    Alert(
                        severity=sev,
                        parameter=key,
                        message=f"{key} exceeds EPA maximum ({hi} {limits['unit']})",
                        value=reading.value,
                        threshold=hi,
                    )
                )
        return alerts

    def detect_anomalies(self, sample: WaterSample) -> list[Alert]:
        """Flag readings that are statistical outliers (modified Z-score)."""
        alerts: list[Alert] = []
        for reading in sample.readings:
            key = reading.sensor_type.value
            history = self._history.get(key, [])
            if len(history) < 10:
                continue  # not enough data
            arr = np.array(history)
            median = float(np.median(arr))
            mad = float(np.median(np.abs(arr - median)))
            if mad == 0:
                continue
            modified_z = 0.6745 * (reading.value - median) / mad
            if abs(modified_z) > self.z_threshold:
                alerts.append(
                    Alert(
                        severity=AlertSeverity.WARNING,
                        parameter=key,
                        message=(
                            f"Anomalous {key} reading (modified Z-score: "
                            f"{modified_z:.1f})"
                        ),
                        value=reading.value,
                        threshold=self.z_threshold,
                    )
                )
        return alerts

    def analyze(self, sample: WaterSample) -> list[Alert]:
        """Run both threshold and anomaly detection, record sample, return alerts."""
        alerts = self.check_thresholds(sample)
        alerts.extend(self.detect_anomalies(sample))
        self.record_sample(sample)
        return alerts

    def trend_test(self, parameter: str) -> dict:
        """Run a Mann-Kendall trend test on a parameter's history.

        Returns a dict with 'trend' ('increasing', 'decreasing', or 'no_trend'),
        'p_value', and 'tau'.
        """
        history = self._history.get(parameter, [])
        if len(history) < 8:
            return {"trend": "insufficient_data", "p_value": None, "tau": None}

        n = len(history)
        s = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                diff = history[j] - history[i]
                if diff > 0:
                    s += 1
                elif diff < 0:
                    s -= 1

        # Variance of S
        var_s = n * (n - 1) * (2 * n + 5) / 18.0
        if var_s == 0:
            return {"trend": "no_trend", "p_value": 1.0, "tau": 0.0}

        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0.0

        p_value = 2.0 * (1.0 - sp_stats.norm.cdf(abs(z)))
        tau = 2.0 * s / (n * (n - 1))

        if p_value < 0.05:
            trend = "increasing" if s > 0 else "decreasing"
        else:
            trend = "no_trend"

        return {"trend": trend, "p_value": round(p_value, 4), "tau": round(tau, 4)}
