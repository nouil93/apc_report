"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
import os
from typing import Any

import yaml

from .constants import DEFAULT_CONFIG_PATHS
from .models import DeviceConfig


class ConfigError(RuntimeError):
    """Raised when configuration is missing or invalid."""


def candidate_paths() -> list[Path]:
    return [Path(os.path.expanduser(path)) for path in DEFAULT_CONFIG_PATHS]


def load_config(path: str | None = None) -> dict[str, Any]:
    paths = [Path(path)] if path else candidate_paths()
    for config_path in paths:
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            return validate_config(data)
    searched = "\n".join(str(p) for p in paths)
    raise ConfigError(f"No configuration file found. Searched:\n{searched}")


def validate_config(data: dict[str, Any]) -> dict[str, Any]:
    devices = data.get("devices")
    if not devices or not isinstance(devices, list):
        raise ConfigError("Configuration must define a non-empty 'devices' list.")

    normalized_devices: list[DeviceConfig] = []
    verify_default = bool(data.get("verify_tls_default", True))

    for index, device in enumerate(devices, start=1):
        missing = [field for field in ("name", "url", "username", "password") if field not in device]
        if missing:
            raise ConfigError(f"Device #{index} is missing required fields: {', '.join(missing)}")
        normalized_devices.append(
            DeviceConfig(
                name=str(device["name"]),
                url=str(device["url"]).rstrip("/"),
                username=str(device["username"]),
                password=str(device["password"]),
                verify_tls=bool(device.get("verify_tls", verify_default)),
            )
        )

    return {
        "output_dir": str(data.get("output_dir", "./reports")),
        "log_level": str(data.get("log_level", "INFO")).upper(),
        "devices": normalized_devices,
    }
