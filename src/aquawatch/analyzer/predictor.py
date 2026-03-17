"""Quality predictor -- forecast water-quality parameter trends."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import curve_fit


@dataclass
class QualityPredictor:
    """Forecast future water quality readings using curve fitting.

    Maintains a per-parameter time series and fits simple models
    (linear, exponential decay/growth) to predict future values.
    """

    _series: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    # list of (time_index, value) pairs

    def add_observation(self, parameter: str, time_index: float, value: float) -> None:
        """Record an observation for a parameter at a given time index."""
        if parameter not in self._series:
            self._series[parameter] = []
        self._series[parameter].append((time_index, value))

    def add_observations(self, parameter: str, values: list[float]) -> None:
        """Add a list of sequential observations (time indices 0, 1, 2, ...)."""
        start = len(self._series.get(parameter, []))
        for i, v in enumerate(values):
            self.add_observation(parameter, float(start + i), v)

    # ------------------------------------------------------------------
    # Forecasting
    # ------------------------------------------------------------------

    @staticmethod
    def _linear(x: np.ndarray, a: float, b: float) -> np.ndarray:
        return a * x + b

    @staticmethod
    def _exponential(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
        return a * np.exp(b * x) + c

    def forecast(
        self,
        parameter: str,
        steps_ahead: int = 5,
        method: str = "linear",
    ) -> list[float]:
        """Predict future values for a parameter.

        Parameters
        ----------
        parameter:
            The parameter name to forecast.
        steps_ahead:
            Number of future time steps to predict.
        method:
            ``"linear"`` or ``"exponential"``.

        Returns
        -------
        List of predicted values for the next ``steps_ahead`` time indices.
        """
        series = self._series.get(parameter, [])
        if len(series) < 3:
            raise ValueError(
                f"Need at least 3 observations for {parameter}, "
                f"have {len(series)}"
            )

        times = np.array([t for t, _ in series])
        values = np.array([v for _, v in series])

        last_time = times[-1]
        future_times = np.array(
            [last_time + i + 1 for i in range(steps_ahead)]
        )

        if method == "exponential":
            try:
                popt, _ = curve_fit(
                    self._exponential, times, values,
                    p0=[1.0, 0.01, values.mean()],
                    maxfev=5000,
                )
                predictions = self._exponential(future_times, *popt)
            except RuntimeError:
                # Fall back to linear if exponential fit fails
                popt, _ = curve_fit(self._linear, times, values)
                predictions = self._linear(future_times, *popt)
        else:
            popt, _ = curve_fit(self._linear, times, values)
            predictions = self._linear(future_times, *popt)

        return [round(float(v), 4) for v in predictions]

    def moving_average(self, parameter: str, window: int = 5) -> list[float]:
        """Compute a simple moving average over the parameter's history."""
        series = self._series.get(parameter, [])
        values = [v for _, v in series]
        if len(values) < window:
            return values
        kernel = np.ones(window) / window
        smoothed = np.convolve(values, kernel, mode="valid")
        return [round(float(v), 4) for v in smoothed]

    def rate_of_change(self, parameter: str, window: int = 5) -> float | None:
        """Average rate of change over the most recent ``window`` readings."""
        series = self._series.get(parameter, [])
        if len(series) < 2:
            return None
        recent = series[-window:]
        if len(recent) < 2:
            return None
        t0, v0 = recent[0]
        t1, v1 = recent[-1]
        dt = t1 - t0
        if dt == 0:
            return None
        return round((v1 - v0) / dt, 4)
