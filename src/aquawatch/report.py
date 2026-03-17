"""Rich-formatted water quality reports."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aquawatch.models import (
    Alert,
    AlertSeverity,
    QualityRating,
    QualityReport,
    WaterSample,
)
from aquawatch.analyzer.quality_index import WaterQualityIndex


def _rating_color(rating: QualityRating) -> str:
    return {
        QualityRating.EXCELLENT: "green",
        QualityRating.GOOD: "blue",
        QualityRating.MEDIUM: "yellow",
        QualityRating.BAD: "red",
        QualityRating.VERY_BAD: "bold red",
    }[rating]


def _severity_color(severity: AlertSeverity) -> str:
    return {
        AlertSeverity.INFO: "cyan",
        AlertSeverity.WARNING: "yellow",
        AlertSeverity.CRITICAL: "bold red",
    }[severity]


def build_report(
    sample: WaterSample,
    alerts: list[Alert] | None = None,
) -> QualityReport:
    """Build a QualityReport from a WaterSample."""
    wqi_calc = WaterQualityIndex()
    score, param_scores = wqi_calc.compute(sample)
    rating = wqi_calc.classify(score)

    recommendations: list[str] = []
    if rating in (QualityRating.BAD, QualityRating.VERY_BAD):
        recommendations.append("Water is unsafe for consumption. Investigate source of contamination.")
    if sample.ph is not None and not (6.5 <= sample.ph <= 8.5):
        recommendations.append(f"pH {sample.ph} is outside acceptable range (6.5-8.5). Check for acid/alkaline discharge.")
    if sample.turbidity is not None and sample.turbidity > 1.0:
        recommendations.append(f"Turbidity {sample.turbidity} NTU exceeds EPA limit. Consider filtration.")
    if sample.dissolved_oxygen is not None and sample.dissolved_oxygen < 4.0:
        recommendations.append(f"DO {sample.dissolved_oxygen} mg/L is critically low. Check for organic pollution or algal bloom.")
    if sample.conductivity is not None and sample.conductivity > 800:
        recommendations.append(f"Conductivity {sample.conductivity} uS/cm exceeds EPA guideline. Check dissolved mineral levels.")

    return QualityReport(
        sample=sample,
        wqi_score=score,
        rating=rating,
        parameter_scores=param_scores,
        alerts=alerts or [],
        recommendations=recommendations,
    )


def print_report(report: QualityReport, console: Console | None = None) -> None:
    """Render a QualityReport to the terminal using Rich."""
    if console is None:
        console = Console()

    # Header
    color = _rating_color(report.rating)
    header = Text()
    header.append("AQUAWATCH Water Quality Report\n", style="bold")
    header.append(f"Sample: {report.sample.sample_id}  ")
    header.append(f"Location: {report.sample.location}  ")
    header.append(f"Time: {report.sample.timestamp:%Y-%m-%d %H:%M}")
    console.print(Panel(header, border_style=color))

    # WQI score
    score_text = Text()
    score_text.append(f"WQI Score: {report.wqi_score:.1f} / 100  ", style="bold")
    score_text.append(f"Rating: {report.rating.value.upper()}", style=color)
    console.print(score_text)
    console.print()

    # Parameter table
    table = Table(title="Sensor Readings & Sub-Index Scores")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Unit")
    table.add_column("Sub-Index", justify="right")

    for reading in report.sample.readings:
        key = reading.sensor_type.value
        qi = report.parameter_scores.get(key)
        qi_str = f"{qi:.1f}" if qi is not None else "-"
        table.add_row(key, f"{reading.value:.2f}", reading.unit, qi_str)

    console.print(table)
    console.print()

    # Alerts
    if report.alerts:
        alert_table = Table(title="Alerts", border_style="red")
        alert_table.add_column("Severity")
        alert_table.add_column("Parameter")
        alert_table.add_column("Message")
        for alert in report.alerts:
            sev_color = _severity_color(alert.severity)
            alert_table.add_row(
                Text(alert.severity.value.upper(), style=sev_color),
                alert.parameter,
                alert.message,
            )
        console.print(alert_table)
        console.print()

    # Recommendations
    if report.recommendations:
        console.print("[bold]Recommendations:[/bold]")
        for rec in report.recommendations:
            console.print(f"  - {rec}")
        console.print()
