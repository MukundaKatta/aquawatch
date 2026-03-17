"""Tests for the report module."""

from aquawatch.models import SensorReading, SensorType, WaterSample, QualityRating
from aquawatch.report import build_report, print_report


def _make_sample(ph=7.0, turb=1.0, do=8.0, temp=15.0, ec=300.0) -> WaterSample:
    return WaterSample(
        sample_id="rpt-test",
        readings=[
            SensorReading(sensor_type=SensorType.PH, value=ph, unit="pH"),
            SensorReading(sensor_type=SensorType.TURBIDITY, value=turb, unit="NTU"),
            SensorReading(sensor_type=SensorType.DISSOLVED_OXYGEN, value=do, unit="mg/L"),
            SensorReading(sensor_type=SensorType.TEMPERATURE, value=temp, unit="C"),
            SensorReading(sensor_type=SensorType.CONDUCTIVITY, value=ec, unit="uS/cm"),
        ],
    )


def test_build_report_clean_water():
    sample = _make_sample()
    report = build_report(sample)
    assert report.wqi_score > 0
    assert report.rating in list(QualityRating)
    assert report.sample.sample_id == "rpt-test"


def test_build_report_generates_recommendations_for_bad_water():
    sample = _make_sample(ph=4.0, turb=50.0, do=2.0, ec=1500.0)
    report = build_report(sample)
    assert len(report.recommendations) > 0


def test_print_report_does_not_crash(capsys):
    """Smoke test: print_report should not raise."""
    from rich.console import Console

    sample = _make_sample()
    report = build_report(sample)
    console = Console(file=None, force_terminal=False, no_color=True, width=120)
    # Just verify no exception is raised
    print_report(report, console)
