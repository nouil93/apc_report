"""CLI entry point."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import ConfigError, load_config
from .models import DeviceConfig
from .reporting import export_csv, generate_pdf_report, generate_plotly_svg
from .scraper import ApcClient, ApcScrapeError
from .utils import calculate_min_max_by_day, configure_logging

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apc-report",
        description="Collect APC UPS telemetry and generate PDF monitoring reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="Path to configuration YAML file.")
    common.add_argument("--device", help="Only run for a single configured device name.")
    common.add_argument("--output-dir", help="Override output directory from config.")

    report_parser = subparsers.add_parser("report", parents=[common], help="Collect data and generate PDF reports.")
    report_parser.set_defaults(func=run_report)

    collect_parser = subparsers.add_parser("collect", parents=[common], help="Collect data and optionally export CSV.")
    collect_parser.add_argument("--csv", action="store_true", help="Export collected telemetry to CSV.")
    collect_parser.set_defaults(func=run_collect)

    return parser


def _selected_devices(devices: list[DeviceConfig], name: str | None) -> list[DeviceConfig]:
    if name is None:
        return devices
    selected = [device for device in devices if device.name == name]
    if not selected:
        raise ConfigError(f"Device '{name}' was not found in configuration.")
    return selected


def run_report(args: argparse.Namespace, config: dict) -> int:
    output_dir = Path(args.output_dir or config["output_dir"])
    for device in _selected_devices(config["devices"], args.device):
        LOGGER.info("Generating report for %s", device.name)
        frame = ApcClient(device).collect_dataframe()
        summary = calculate_min_max_by_day(frame)
        chart = generate_plotly_svg(frame, device.name)
        csv_path = export_csv(frame, output_dir, device.name)
        pdf_path = generate_pdf_report(frame, summary, chart, output_dir, device)
        LOGGER.info("Generated CSV: %s", csv_path)
        LOGGER.info("Generated PDF: %s", pdf_path)
    return 0


def run_collect(args: argparse.Namespace, config: dict) -> int:
    output_dir = Path(args.output_dir or config["output_dir"])
    for device in _selected_devices(config["devices"], args.device):
        LOGGER.info("Collecting telemetry for %s", device.name)
        frame = ApcClient(device).collect_dataframe()
        LOGGER.info("Collected %s row(s) for %s", len(frame), device.name)
        if args.csv:
            csv_path = export_csv(frame, output_dir, device.name)
            LOGGER.info("Generated CSV: %s", csv_path)
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        configure_logging(config["log_level"])
        return args.func(args, config)
    except (ConfigError, ApcScrapeError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 2
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Unexpected error: %s", exc)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
