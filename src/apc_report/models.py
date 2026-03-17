"""Data models for configuration."""

from dataclasses import dataclass


@dataclass(slots=True)
class DeviceConfig:
    name: str
    url: str
    username: str
    password: str
    verify_tls: bool = True
