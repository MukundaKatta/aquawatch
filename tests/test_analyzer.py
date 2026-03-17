"""Tests for analyzer modules."""

import pytest

from aquawatch.analyzer.quality_index import WaterQualityIndex
from aquawatch.analyzer.contamination import ContaminationDetector
from aquawatch.analyzer.predictor import QualityPredictor
from aquawatch.models import (
    AlertSeverity,
    QualityRating,
    SensorReading,
    SensorType,
    WaterSample,
)


def _make_sample(
    ph=7.0, turbidity=1.0, do=8.0, temperature=15.0, conductivity=300.0
) -> WaterSample:
    """Helper to build a WaterSample with all five readings."""
    return WaterSample(
        sample_id="test",
        readings=[
            SensorReading(sensor_type=SensorType.PH, value=ph, unit="pH"),
            SensorReading(sensor_type=SensorType.TURBIDITY, value=turbidity, unit="NTU"),
            SensorReading(sensor_type=SensorType.DISSOLVED_OXYGEN, value=do, unit="mg/L"),
            SensorReading(sensor_type=SensorType.TEMPERATURE, value=temperature, unit="C"),
            SensorReading(sensor_type=SensorType.CONDUCTIVITY, value=conductivity, unit="uS/cm"),
        ],
    )


class TestWaterQualityIndex:
    def test_clean_water_high_score(self):
        wqi = WaterQualityIndex()
        sample = _make_sample(ph=7.0, turbidity=0.5, do=9.5, temperature=15.0, conductivity=200.0)
        score, scores = wqi.compute(sample)
        assert score >= 70
        assert "ph" in scores
        assert "turbidity" in scores

    def test_polluted_water_low_score(self):
        wqi = WaterQualityIndex()
        sample = _make_sample(ph=4.0, turbidity=100.0, do=2.0, temperature=35.0, conductivity=2000.0)
        score, _ = wqi.compute(sample)
        assert score < 30

    def test_classify_excellent(self):
        assert WaterQualityIndex.classify(95.0) == QualityRating.EXCELLENT

    def test_classify_good(self):
        assert WaterQualityIndex.classify(80.0) == QualityRating.GOOD

    def test_classify_medium(self):
        assert WaterQualityIndex.classify(60.0) == QualityRating.MEDIUM

    def test_classify_bad(self):
        assert WaterQualityIndex.classify(40.0) == QualityRating.BAD

    def test_classify_very_bad(self):
        assert WaterQualityIndex.classify(15.0) == QualityRating.VERY_BAD

    def test_empty_sample_returns_zero(self):
        wqi = WaterQualityIndex()
        sample = WaterSample(sample_id="empty")
        score, scores = wqi.compute(sample)
        assert score == 0.0
        assert scores == {}

    def test_partial_sample(self):
        """WQI should work with fewer than 5 parameters."""
        wqi = WaterQualityIndex()
        sample = WaterSample(
            sample_id="partial",
            readings=[
                SensorReading(sensor_type=SensorType.PH, value=7.0, unit="pH"),
            ],
        )
        score, scores = wqi.compute(sample)
        assert 0 <= score <= 100
        assert "ph" in scores

    def test_score_bounded(self):
        wqi = WaterQualityIndex()
        sample = _make_sample()
        score, _ = wqi.compute(sample)
        assert 0 <= score <= 100


class TestContaminationDetector:
    def test_threshold_alert_low_ph(self):
        detector = ContaminationDetector()
        sample = _make_sample(ph=3.0)
        alerts = detector.check_thresholds(sample)
        ph_alerts = [a for a in alerts if a.parameter == "ph"]
        assert len(ph_alerts) >= 1
        assert ph_alerts[0].severity == AlertSeverity.CRITICAL

    def test_threshold_alert_high_turbidity(self):
        detector = ContaminationDetector()
        sample = _make_sample(turbidity=5.0)
        alerts = detector.check_thresholds(sample)
        turb_alerts = [a for a in alerts if a.parameter == "turbidity"]
        assert len(turb_alerts) >= 1

    def test_no_alerts_for_clean_water(self):
        detector = ContaminationDetector()
        sample = _make_sample(ph=7.0, turbidity=0.5, do=8.0, temperature=20.0, conductivity=300.0)
        alerts = detector.check_thresholds(sample)
        assert len(alerts) == 0

    def test_anomaly_detection_flags_outlier(self):
        detector = ContaminationDetector(z_threshold=2.5, window_size=20)
        # Build stable history
        for _ in range(20):
            stable = _make_sample(ph=7.0)
            detector.record_sample(stable)
        # Now introduce anomaly
        anomalous = _make_sample(ph=3.0)
        alerts = detector.detect_anomalies(anomalous)
        ph_anomalies = [a for a in alerts if a.parameter == "ph"]
        assert len(ph_anomalies) >= 1

    def test_trend_test_insufficient_data(self):
        detector = ContaminationDetector()
        result = detector.trend_test("ph")
        assert result["trend"] == "insufficient_data"

    def test_trend_test_increasing(self):
        detector = ContaminationDetector()
        for i in range(20):
            reading = SensorReading(
                sensor_type=SensorType.PH, value=6.0 + i * 0.1, unit="pH"
            )
            detector.record(reading)
        result = detector.trend_test("ph")
        assert result["trend"] == "increasing"

    def test_analyze_records_and_returns(self):
        detector = ContaminationDetector()
        sample = _make_sample(ph=3.0)
        alerts = detector.analyze(sample)
        assert isinstance(alerts, list)
        # History should now be populated
        assert len(detector._history["ph"]) == 1


class TestQualityPredictor:
    def test_linear_forecast(self):
        pred = QualityPredictor()
        # Linear: y = 2x + 1
        for i in range(10):
            pred.add_observation("ph", float(i), 2.0 * i + 1.0)
        forecast = pred.forecast("ph", steps_ahead=3, method="linear")
        assert len(forecast) == 3
        # Next values should be near 21, 23, 25
        assert abs(forecast[0] - 21.0) < 1.0

    def test_forecast_insufficient_data(self):
        pred = QualityPredictor()
        pred.add_observation("ph", 0.0, 7.0)
        with pytest.raises(ValueError, match="at least 3"):
            pred.forecast("ph")

    def test_add_observations(self):
        pred = QualityPredictor()
        pred.add_observations("ph", [7.0, 7.1, 7.2, 7.3])
        assert len(pred._series["ph"]) == 4

    def test_moving_average(self):
        pred = QualityPredictor()
        pred.add_observations("ph", [7.0, 7.2, 7.4, 7.6, 7.8, 8.0])
        ma = pred.moving_average("ph", window=3)
        assert len(ma) == 4  # 6 - 3 + 1
        assert abs(ma[0] - 7.2) < 0.01  # mean of 7.0, 7.2, 7.4

    def test_rate_of_change(self):
        pred = QualityPredictor()
        pred.add_observations("ph", [7.0, 7.1, 7.2, 7.3, 7.4])
        roc = pred.rate_of_change("ph")
        assert roc is not None
        assert abs(roc - 0.1) < 0.01

    def test_rate_of_change_insufficient(self):
        pred = QualityPredictor()
        assert pred.rate_of_change("ph") is None

    def test_exponential_forecast(self):
        pred = QualityPredictor()
        # Gently increasing exponential
        for i in range(15):
            pred.add_observation("turb", float(i), 1.0 + 0.5 * i + 0.01 * i * i)
        forecast = pred.forecast("turb", steps_ahead=3, method="exponential")
        assert len(forecast) == 3
        # Values should be increasing
        assert forecast[2] > forecast[0]
