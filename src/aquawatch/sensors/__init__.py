"""Sensor modules for water quality monitoring."""

from aquawatch.sensors.ph import PHMonitor
from aquawatch.sensors.turbidity import TurbidityMonitor
from aquawatch.sensors.dissolved_oxygen import DOMonitor
from aquawatch.sensors.temperature import TemperatureMonitor
from aquawatch.sensors.conductivity import ConductivityMonitor

__all__ = [
    "PHMonitor",
    "TurbidityMonitor",
    "DOMonitor",
    "TemperatureMonitor",
    "ConductivityMonitor",
]
