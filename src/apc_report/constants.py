"""Project constants."""

DEFAULT_CONFIG_PATHS = [
    "./config.yaml",
    "~/.config/apc-report/config.yaml",
    "/etc/apc-report/config.yaml",
]

EXPECTED_COLUMNS = [
    "date",
    "time",
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
