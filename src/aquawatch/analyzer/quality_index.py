"""NSF Water Quality Index (WQI) computation.

The National Sanitation Foundation WQI aggregates sub-index scores for
individual parameters into a single 0-100 score using weighted averaging.

Reference weights (Brown et al., 1970):
    DO            0.17
    Fecal Coliform 0.16  (not modelled here; weight redistributed)
    pH            0.11
    BOD           0.11  (approximated via turbidity proxy)
    Temperature   0.10
    Turbidity     0.08
    Total Solids  0.07  (approximated via conductivity)
    Nitrates      0.10  (not modelled; weight redistributed)
    Phosphates    0.10  (not modelled; weight redistributed)

We redistribute the three missing parameters' weights proportionally
across the five parameters we do measure.
"""

from __future__ import annotations

import numpy as np

from aquawatch.models import (
    QualityRating,
    WaterSample,
)


# Original NSF weights for the parameters we model
_RAW_WEIGHTS = {
    "dissolved_oxygen": 0.17,
    "ph": 0.11,
    "temperature": 0.10,
    "turbidity": 0.08 + 0.11,  # turbidity absorbs BOD proxy weight
    "conductivity": 0.07,  # proxy for total solids
}

# Normalise so weights sum to 1.0
_WEIGHT_SUM = sum(_RAW_WEIGHTS.values())
WEIGHTS: dict[str, float] = {k: v / _WEIGHT_SUM for k, v in _RAW_WEIGHTS.items()}


class WaterQualityIndex:
    """Compute the NSF-WQI from a WaterSample."""

    # ------------------------------------------------------------------
    # Sub-index curves (piece-wise linear approximations of NSF Q-curves)
    # ------------------------------------------------------------------

    @staticmethod
    def _q_do(do_pct_sat: float) -> float:
        """Sub-index for dissolved oxygen (% saturation)."""
        if do_pct_sat <= 0:
            return 0.0
        if do_pct_sat >= 140:
            return 50.0
        # Piece-wise linear approximation of the NSF DO Q-curve
        breakpoints = [
            (0, 0), (10, 5), (20, 10), (40, 25), (60, 42),
            (80, 68), (100, 95), (120, 85), (140, 50),
        ]
        return float(np.interp(do_pct_sat, [b[0] for b in breakpoints], [b[1] for b in breakpoints]))

    @staticmethod
    def _q_ph(ph: float) -> float:
        """Sub-index for pH."""
        breakpoints = [
            (2, 0), (4, 5), (5, 20), (6, 45), (6.5, 60),
            (7, 90), (7.5, 95), (8, 85), (8.5, 72),
            (9, 55), (10, 30), (12, 5), (14, 0),
        ]
        return float(np.interp(ph, [b[0] for b in breakpoints], [b[1] for b in breakpoints]))

    @staticmethod
    def _q_turbidity(ntu: float) -> float:
        """Sub-index for turbidity (NTU)."""
        breakpoints = [
            (0, 98), (5, 80), (10, 65), (25, 50),
            (50, 35), (100, 15), (200, 5), (500, 2),
        ]
        return float(np.interp(ntu, [b[0] for b in breakpoints], [b[1] for b in breakpoints]))

    @staticmethod
    def _q_temperature_change(delta_c: float) -> float:
        """Sub-index for temperature deviation from natural baseline (15 C)."""
        delta = abs(delta_c)
        breakpoints = [
            (0, 93), (2, 85), (5, 70), (10, 50),
            (15, 30), (20, 15), (30, 5),
        ]
        return float(np.interp(delta, [b[0] for b in breakpoints], [b[1] for b in breakpoints]))

    @staticmethod
    def _q_conductivity(us_cm: float) -> float:
        """Sub-index for conductivity / total solids proxy."""
        breakpoints = [
            (0, 80), (100, 78), (200, 72), (400, 60),
            (600, 48), (800, 35), (1200, 20), (2000, 8), (5000, 2),
        ]
        return float(np.interp(us_cm, [b[0] for b in breakpoints], [b[1] for b in breakpoints]))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(
        self,
        sample: WaterSample,
        *,
        baseline_temp: float = 15.0,
        do_saturation_pct: float | None = None,
    ) -> tuple[float, dict[str, float]]:
        """Compute the WQI score for a water sample.

        Parameters
        ----------
        sample:
            WaterSample containing sensor readings.
        baseline_temp:
            Natural/reference water temperature in Celsius for the
            temperature-change sub-index.  Default 15 C (temperate stream).
        do_saturation_pct:
            If provided, use this as DO % saturation directly.
            Otherwise, estimate from DO mg/L and temperature using
            the Benson-Krause saturation formula.

        Returns
        -------
        (wqi_score, parameter_scores) where parameter_scores maps each
        parameter name to its sub-index value (0-100).
        """
        from aquawatch.sensors.dissolved_oxygen import DOMonitor

        scores: dict[str, float] = {}

        # Dissolved oxygen
        do = sample.dissolved_oxygen
        temp = sample.temperature
        if do is not None:
            if do_saturation_pct is not None:
                pct = do_saturation_pct
            elif temp is not None:
                sat = DOMonitor.saturation_concentration(temp)
                pct = (do / sat) * 100.0 if sat > 0 else 0.0
            else:
                # Assume 25 C if temperature unavailable
                sat = DOMonitor.saturation_concentration(25.0)
                pct = (do / sat) * 100.0 if sat > 0 else 0.0
            scores["dissolved_oxygen"] = self._q_do(pct)

        # pH
        ph = sample.ph
        if ph is not None:
            scores["ph"] = self._q_ph(ph)

        # Turbidity
        turb = sample.turbidity
        if turb is not None:
            scores["turbidity"] = self._q_turbidity(turb)

        # Temperature change
        if temp is not None:
            scores["temperature"] = self._q_temperature_change(temp - baseline_temp)

        # Conductivity
        ec = sample.conductivity
        if ec is not None:
            scores["conductivity"] = self._q_conductivity(ec)

        if not scores:
            return 0.0, scores

        # Weighted aggregation (renormalise weights for available params)
        available_weight = sum(WEIGHTS[k] for k in scores)
        wqi = sum(WEIGHTS[k] / available_weight * scores[k] for k in scores)
        wqi = round(min(max(wqi, 0.0), 100.0), 1)

        return wqi, scores

    @staticmethod
    def classify(wqi: float) -> QualityRating:
        """Classify a WQI score into a quality rating."""
        if wqi >= 91:
            return QualityRating.EXCELLENT
        if wqi >= 71:
            return QualityRating.GOOD
        if wqi >= 51:
            return QualityRating.MEDIUM
        if wqi >= 26:
            return QualityRating.BAD
        return QualityRating.VERY_BAD
