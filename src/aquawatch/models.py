"""Pydantic models for AQUAWATCH water quality data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SensorType(str, Enum):
    """Types of water quality sensors."""

    PH = "ph"
    TURBIDITY = "turbidity"
    DISSOLVED_OXYGEN = "dissolved_oxygen"
    TEMPERATURE = "temperature"
    CONDUCTIVITY = "conductivity"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class QualityRating(str, Enum):
    """Water quality rating per NSF-WQI classification."""

    EXCELLENT = "excellent"  # 91-100
    GOOD = "good"  # 71-90
    MEDIUM = "medium"  # 51-70
    BAD = "bad"  # 26-50
    VERY_BAD = "very_bad"  # 0-25


class SensorReading(BaseModel):
    """A single reading from a water quality sensor."""

    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.now)
    location: str = "default"
    is_valid: bool = True
    error_margin: float = 0.0

    def __repr__(self) -> str:
        return f"SensorReading({self.sensor_type.value}={self.value}{self.unit})"


class WaterSample(BaseModel):
    """A collection of sensor readings representing one water sample."""

    sample_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    location: str = "default"
    readings: list[SensorReading] = Field(default_factory=list)

    def get_reading(self, sensor_type: SensorType) -> Optional[SensorReading]:
        """Retrieve a reading by sensor type."""
        for r in self.readings:
            if r.sensor_type == sensor_type:
                return r
        return None

    @property
    def ph(self) -> Optional[float]:
        r = self.get_reading(SensorType.PH)
        return r.value if r else None

    @property
    def turbidity(self) -> Optional[float]:
        r = self.get_reading(SensorType.TURBIDITY)
        return r.value if r else None

    @property
    def dissolved_oxygen(self) -> Optional[float]:
        r = self.get_reading(SensorType.DISSOLVED_OXYGEN)
        return r.value if r else None

    @property
    def temperature(self) -> Optional[float]:
        r = self.get_reading(SensorType.TEMPERATURE)
        return r.value if r else None

    @property
    def conductivity(self) -> Optional[float]:
        r = self.get_reading(SensorType.CONDUCTIVITY)
        return r.value if r else None


class QualityReport(BaseModel):
    """Water quality assessment report."""

    sample: WaterSample
    wqi_score: float = Field(ge=0, le=100)
    rating: QualityRating
    parameter_scores: dict[str, float] = Field(default_factory=dict)
    alerts: list[Alert] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    recommendations: list[str] = Field(default_factory=list)


class Alert(BaseModel):
    """An alert triggered by abnormal water quality conditions."""

    severity: AlertSeverity
    parameter: str
    message: str
    value: float
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.now)


# Rebuild QualityReport to resolve the forward reference to Alert
QualityReport.model_rebuild()


# ---------------------------------------------------------------------------
# EPA / WHO reference thresholds
# ---------------------------------------------------------------------------

# EPA National Primary/Secondary Drinking Water Standards & WHO Guidelines
EPA_THRESHOLDS = {
    "ph": {"min": 6.5, "max": 8.5, "unit": "pH"},
    "turbidity": {"max": 1.0, "unit": "NTU"},  # EPA MCL for surface-water treatment
    "dissolved_oxygen": {"min": 4.0, "unit": "mg/L"},  # EPA aquatic-life criterion
    "temperature": {"max": 30.0, "unit": "C"},  # general warm-water aquatic limit
    "conductivity": {"max": 800.0, "unit": "uS/cm"},  # EPA secondary guideline
}

WHO_THRESHOLDS = {
    "ph": {"min": 6.5, "max": 8.5, "unit": "pH"},
    "turbidity": {"max": 4.0, "unit": "NTU"},  # WHO guideline
    "dissolved_oxygen": {"min": 5.0, "unit": "mg/L"},
    "temperature": {"max": 25.0, "unit": "C"},
    "conductivity": {"max": 1000.0, "unit": "uS/cm"},
}
