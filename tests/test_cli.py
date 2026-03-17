"""Tests for the CLI module."""

from click.testing import CliRunner

from aquawatch.cli import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_monitor():
    runner = CliRunner()
    result = runner.invoke(cli, ["monitor", "--profile", "clean_river"])
    assert result.exit_code == 0


def test_cli_analyze():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "7.0", "1.0", "8.0", "20.0", "300.0"])
    assert result.exit_code == 0


def test_cli_timeseries():
    runner = CliRunner()
    result = runner.invoke(cli, ["timeseries", "--samples", "10", "--seed", "42"])
    assert result.exit_code == 0
