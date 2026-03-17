# AQUAWATCH - Water Quality Monitor

Real-time water quality monitoring, contamination detection, and quality forecasting.

## Features

- **Five-sensor monitoring** -- pH (with multi-point calibration), turbidity, dissolved oxygen, temperature, electrical conductivity
- **NSF Water Quality Index** -- computes a single 0-100 score from sensor readings using the NSF-WQI weighted sub-index formula
- **Contamination detection** -- threshold checks against EPA/WHO standards plus statistical anomaly detection (modified Z-score)
- **Trend forecasting** -- linear and exponential curve fitting, moving averages, Mann-Kendall trend tests
- **Rich CLI** -- terminal reports with color-coded ratings, alerts, and recommendations
- **Realistic simulation** -- four water-body profiles (clean river, urban stream, polluted lake, drinking water) with configurable drift

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# Simulated monitoring with a Rich report
aquawatch monitor --profile clean_river

# Analyze manual readings: pH turbidity DO temperature conductivity
aquawatch analyze 7.2 0.8 8.5 18.0 350.0

# Time-series trend analysis
aquawatch timeseries --profile urban_stream --samples 48 --seed 42
```

## Project Structure

```
src/aquawatch/
  cli.py                    Click CLI
  models.py                 Pydantic models + EPA/WHO thresholds
  simulator.py              Realistic data generator
  report.py                 Rich-formatted reports
  sensors/
    ph.py                   PHMonitor (multi-point calibration)
    turbidity.py            TurbidityMonitor
    dissolved_oxygen.py     DOMonitor (Benson-Krause saturation)
    temperature.py          TemperatureMonitor
    conductivity.py         ConductivityMonitor (TDS estimation)
  analyzer/
    quality_index.py        WaterQualityIndex (NSF-WQI)
    contamination.py        ContaminationDetector (threshold + anomaly)
    predictor.py            QualityPredictor (forecast + moving avg)
tests/
  test_models.py
  test_sensors.py
  test_analyzer.py
  test_simulator.py
  test_report.py
  test_cli.py
```

## Running Tests

```bash
pytest
```

## Author

Mukunda Katta
