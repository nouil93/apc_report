import pandas as pd

from apc_report.utils import calculate_min_max_by_day, is_date_string, normalize_dataframe


def test_is_date_string_accepts_expected_formats():
    assert is_date_string("03/16/2026")
    assert is_date_string("2026-03-16")
    assert not is_date_string("16-03-2026")


def test_normalize_dataframe_builds_timestamp_and_numeric_columns():
    df = pd.DataFrame(
        [
            {
                "date": "03/16/2026",
                "time": "12:00:00",
                "vmin": "119.1",
                "vmax": "121.2",
                "vout": "120.0",
                "iout": "2.1",
                "pct_wout": "16",
                "pct_out": "12",
                "freq_out": "60.0",
                "pct_cap": "88",
                "vbat": "54.1",
                "temp_ups_c": "28.1",
                "temp_ambient_c": "24.4",
                "humidity_ambient_pct": "37",
            }
        ]
    )
    normalized = normalize_dataframe(df)
    assert "timestamp" in normalized.columns
    assert normalized.loc[0, "temp_ambient_c"] == 24.4


def test_calculate_min_max_by_day_returns_expected_columns():
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-03-16 10:00:00", "2026-03-16 12:00:00"]),
            "temp_ups_c": [28.0, 31.0],
            "temp_ambient_c": [23.0, 25.0],
        }
    )
    result = calculate_min_max_by_day(df)
    assert list(result.columns) == ["date", "temp_ups_min", "temp_ups_max", "temp_ambient_min", "temp_ambient_max"]
