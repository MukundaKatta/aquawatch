"""Analysis modules for water quality assessment."""

from aquawatch.analyzer.quality_index import WaterQualityIndex
from aquawatch.analyzer.contamination import ContaminationDetector
from aquawatch.analyzer.predictor import QualityPredictor

__all__ = [
    "WaterQualityIndex",
    "ContaminationDetector",
    "QualityPredictor",
]
