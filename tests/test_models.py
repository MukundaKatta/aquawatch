"""Tests for pydantic models."""

from datetime import datetime

from aquawatch.models import (
    Alert,
    AlertSeverity,
    QualityRating,
    QualityReport,
    SensorReading,
    SensorType,
    WaterSample,
)


def test_sensor_reading_creation():
    r = SensorReading(sensor_type=SensorType.PH, value=7.0, unit="pH")
    assert r.value == 7.0
    assert r.sensor_type == SensorType.PH
    assert r.is_valid is True


def test_water_sample_get_reading():
    readings = [
        SensorReading(sensor_type=SensorType.PH, value=7.2, unit="pH"),
        SensorReading(sensor_type=SensorType.TURBIDITY, value=3.0, unit="NTU"),
    ]
    sample = WaterSample(sample_id="test-001", readings=readings)
    assert sample.ph == 7.2
    assert sample.turbidity == 3.0
    assert sample.dissolved_oxygen is None


def test_water_sample_get_reading_returns_none():
    sample = WaterSample(sample_id="empty")
    assert sample.get_reading(SensorType.PH) is None


def test_alert_creation():
    a = Alert(
        severity=AlertSeverity.CRITICAL,
        parameter="ph",
        message="pH too low",
        value=3.0,
        threshold=6.5,
    )
    assert a.severity == AlertSeverity.CRITICAL
    assert a.value == 3.0


def test_quality_rating_values():
    assert QualityRating.EXCELLENT.value == "excellent"
    assert QualityRating.VERY_BAD.value == "very_bad"


def test_quality_report_creation():
    sample = WaterSample(sample_id="rpt-001")
    report = QualityReport(
        sample=sample,
        wqi_score=75.0,
        rating=QualityRating.GOOD,
    )
    assert report.wqi_score == 75.0
    assert report.rating == QualityRating.GOOD
    assert report.alerts == []
