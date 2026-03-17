"""Tests for sensor modules."""

import pytest

from aquawatch.sensors.ph import PHMonitor
from aquawatch.sensors.turbidity import TurbidityMonitor
from aquawatch.sensors.dissolved_oxygen import DOMonitor
from aquawatch.sensors.temperature import TemperatureMonitor
from aquawatch.sensors.conductivity import ConductivityMonitor
from aquawatch.models import SensorType


class TestPHMonitor:
    def test_uncalibrated_read(self):
        mon = PHMonitor()
        r = mon.read(7.0)
        assert r.sensor_type == SensorType.PH
        assert r.value == 7.0
        assert r.unit == "pH"

    def test_single_point_calibration(self):
        mon = PHMonitor()
        mon.add_calibration_point(6.8, 7.0)
        # offset = 7.0 - 6.8 = 0.2, slope = 1.0
        r = mon.read(7.0)
        assert abs(r.value - 7.2) < 0.01

    def test_two_point_calibration(self):
        mon = PHMonitor()
        # Simulate raw values that map linearly to actual pH
        mon.add_calibration_point(4.0, 4.01)
        mon.add_calibration_point(7.0, 7.00)
        assert mon.is_calibrated
        r = mon.read(7.0)
        assert abs(r.value - 7.0) < 0.1

    def test_calibrate_convenience(self):
        mon = PHMonitor()
        mon.calibrate({"acid": 4.0, "neutral": 7.0, "base": 10.0})
        assert mon.is_calibrated

    def test_calibrate_unknown_buffer_raises(self):
        mon = PHMonitor()
        with pytest.raises(ValueError, match="Unknown buffer"):
            mon.calibrate({"unknown": 5.0})

    def test_check_acceptable(self):
        mon = PHMonitor()
        assert mon.check_acceptable(7.0) is True
        assert mon.check_acceptable(5.0) is False
        assert mon.check_acceptable(9.0) is False

    def test_invalid_ph_range(self):
        mon = PHMonitor()
        r = mon.read(-1.0)
        assert r.is_valid is False
        r = mon.read(15.0)
        assert r.is_valid is False


class TestTurbidityMonitor:
    def test_read(self):
        mon = TurbidityMonitor()
        r = mon.read(0.5)
        assert r.sensor_type == SensorType.TURBIDITY
        assert r.value == 0.5

    def test_check_epa(self):
        mon = TurbidityMonitor()
        assert mon.check_epa(0.5) is True
        assert mon.check_epa(2.0) is False

    def test_check_who(self):
        mon = TurbidityMonitor()
        assert mon.check_who(3.0) is True
        assert mon.check_who(5.0) is False


class TestDOMonitor:
    def test_read(self):
        mon = DOMonitor()
        r = mon.read(8.0)
        assert r.sensor_type == SensorType.DISSOLVED_OXYGEN
        assert r.value == 8.0

    def test_saturation_concentration(self):
        # At ~25 C, DO saturation is roughly 8.2 mg/L
        sat = DOMonitor.saturation_concentration(25.0)
        assert 7.5 < sat < 9.0

    def test_check_healthy(self):
        mon = DOMonitor()
        assert mon.check_healthy(6.0) is True
        assert mon.check_healthy(3.0) is False

    def test_is_hypoxic(self):
        mon = DOMonitor()
        assert mon.is_hypoxic(1.5) is True
        assert mon.is_hypoxic(4.0) is False


class TestTemperatureMonitor:
    def test_read(self):
        mon = TemperatureMonitor()
        r = mon.read(20.0)
        assert r.sensor_type == SensorType.TEMPERATURE
        assert r.value == 20.0

    def test_epa_check(self):
        mon = TemperatureMonitor()
        assert mon.check_epa_warmwater(25.0) is True
        assert mon.check_epa_warmwater(35.0) is False


class TestConductivityMonitor:
    def test_read(self):
        mon = ConductivityMonitor()
        r = mon.read(500.0)
        assert r.sensor_type == SensorType.CONDUCTIVITY
        assert r.value == 500.0

    def test_estimate_tds(self):
        mon = ConductivityMonitor()
        tds = mon.estimate_tds(500.0)
        assert tds == 325.0  # 500 * 0.65

    def test_check_epa(self):
        mon = ConductivityMonitor()
        assert mon.check_epa(700.0) is True
        assert mon.check_epa(900.0) is False
