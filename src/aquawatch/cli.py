"""AQUAWATCH command-line interface."""

from __future__ import annotations

import click
from rich.console import Console

from aquawatch import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="aquawatch")
def cli() -> None:
    """AQUAWATCH - Water Quality Monitor."""


@cli.command()
@click.option(
    "--profile",
    type=click.Choice(["clean_river", "urban_stream", "polluted_lake", "drinking_water"]),
    default="clean_river",
    help="Water body profile for simulation.",
)
@click.option("--location", default="sim", help="Location label.")
def monitor(profile: str, location: str) -> None:
    """Take a simulated reading and generate a quality report."""
    from aquawatch.analyzer.contamination import ContaminationDetector
    from aquawatch.report import build_report, print_report
    from aquawatch.simulator import generate_sample

    sample = generate_sample(profile, location=location)
    detector = ContaminationDetector()
    alerts = detector.analyze(sample)
    report = build_report(sample, alerts)
    print_report(report, console)


@cli.command()
@click.option(
    "--profile",
    type=click.Choice(["clean_river", "urban_stream", "polluted_lake", "drinking_water"]),
    default="urban_stream",
    help="Water body profile.",
)
@click.option("--samples", default=24, type=int, help="Number of samples.")
@click.option("--interval", default=60, type=int, help="Minutes between samples.")
@click.option("--seed", default=42, type=int, help="Random seed.")
def timeseries(profile: str, samples: int, interval: int, seed: int) -> None:
    """Generate a time series and show trend analysis."""
    from rich.table import Table

    from aquawatch.analyzer.contamination import ContaminationDetector
    from aquawatch.analyzer.predictor import QualityPredictor
    from aquawatch.analyzer.quality_index import WaterQualityIndex
    from aquawatch.simulator import generate_time_series

    series = generate_time_series(
        profile, n_samples=samples, interval_minutes=interval, seed=seed
    )

    wqi_calc = WaterQualityIndex()
    detector = ContaminationDetector()
    predictor = QualityPredictor()

    scores = []
    for s in series:
        score, _ = wqi_calc.compute(s)
        scores.append(score)
        detector.record_sample(s)
        for reading in s.readings:
            predictor.add_observation(
                reading.sensor_type.value, s.timestamp.timestamp(), reading.value
            )

    console.print(f"\n[bold]Time Series Analysis[/bold] -- {profile} ({samples} samples)\n")

    table = Table(title="Summary Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Mean WQI", f"{sum(scores) / len(scores):.1f}")
    table.add_row("Min WQI", f"{min(scores):.1f}")
    table.add_row("Max WQI", f"{max(scores):.1f}")
    table.add_row("Std Dev", f"{(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))**0.5:.1f}")
    console.print(table)
    console.print()

    # Trend tests
    trend_table = Table(title="Mann-Kendall Trend Tests")
    trend_table.add_column("Parameter", style="cyan")
    trend_table.add_column("Trend")
    trend_table.add_column("p-value", justify="right")
    trend_table.add_column("Tau", justify="right")
    for param in ["ph", "turbidity", "dissolved_oxygen", "temperature", "conductivity"]:
        result = detector.trend_test(param)
        trend_table.add_row(
            param,
            result["trend"],
            str(result["p_value"]) if result["p_value"] is not None else "-",
            str(result["tau"]) if result["tau"] is not None else "-",
        )
    console.print(trend_table)


@cli.command()
@click.argument("ph", type=float)
@click.argument("turbidity", type=float)
@click.argument("do", type=float)
@click.argument("temperature", type=float)
@click.argument("conductivity", type=float)
@click.option("--location", default="manual", help="Location label.")
def analyze(
    ph: float,
    turbidity: float,
    do: float,
    temperature: float,
    conductivity: float,
    location: str,
) -> None:
    """Analyze manually entered sensor values.

    Usage: aquawatch analyze <pH> <turbidity> <DO> <temperature> <conductivity>
    """
    import uuid
    from datetime import datetime

    from aquawatch.analyzer.contamination import ContaminationDetector
    from aquawatch.models import SensorReading, SensorType, WaterSample
    from aquawatch.report import build_report, print_report

    sample = WaterSample(
        sample_id=str(uuid.uuid4())[:8],
        timestamp=datetime.now(),
        location=location,
        readings=[
            SensorReading(sensor_type=SensorType.PH, value=ph, unit="pH"),
            SensorReading(sensor_type=SensorType.TURBIDITY, value=turbidity, unit="NTU"),
            SensorReading(sensor_type=SensorType.DISSOLVED_OXYGEN, value=do, unit="mg/L"),
            SensorReading(sensor_type=SensorType.TEMPERATURE, value=temperature, unit="C"),
            SensorReading(sensor_type=SensorType.CONDUCTIVITY, value=conductivity, unit="uS/cm"),
        ],
    )

    detector = ContaminationDetector()
    alerts = detector.analyze(sample)
    report = build_report(sample, alerts)
    print_report(report, console)


if __name__ == "__main__":
    cli()
