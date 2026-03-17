"""Utility helpers for parsing and aggregation."""

from __future__ import annotations

import logging
import re

import pandas as pd

DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$|^\d{4}-\d{2}-\d{2}$")


def is_date_string(value: str) -> bool:
    return bool(DATE_PATTERN.match(value.strip()))


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("No data rows were collected from the APC interface.")

    numeric_columns = [
        "vmin",
        "vmax",
        "vout",
        "iout",
        "pct_wout",
        "pct_out",
        "freq_out",
        "pct_cap",
        "vbat",
        "temp_ups_c",
        "temp_ambient_c",
        "humidity_ambient_pct",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).drop(columns=["date", "time"]).sort_values("timestamp")
    return df.reset_index(drop=True)


def calculate_min_max_by_day(df: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "temp_ups_c", "temp_ambient_c"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for daily min/max calculation: {', '.join(sorted(missing))}")

    working = df.copy()
    working["date"] = working["timestamp"].dt.date
    result = (
        working.groupby("date")
        .agg(
            temp_ups_min=("temp_ups_c", "min"),
            temp_ups_max=("temp_ups_c", "max"),
            temp_ambient_min=("temp_ambient_c", "min"),
            temp_ambient_max=("temp_ambient_c", "max"),
        )
        .reset_index()
    )
    return result


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
