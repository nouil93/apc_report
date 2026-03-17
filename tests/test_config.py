import pytest

from apc_report.config import ConfigError, validate_config


def test_validate_config_requires_devices():
    with pytest.raises(ConfigError):
        validate_config({})


def test_validate_config_normalizes_devices():
    config = validate_config(
        {
            "devices": [
                {
                    "name": "rack-a",
                    "url": "https://example.local/",
                    "username": "user",
                    "password": "pass",
                }
            ]
        }
    )
    assert config["devices"][0].url == "https://example.local"
