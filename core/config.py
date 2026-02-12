#!/usr/bin/env python3
import json
import os
from pathlib import Path


DEFAULT_API_BASE = "https://api.gptsapi.net/api/v3"
DEFAULT_PROVIDER = "google"
DEFAULT_MODEL = "gemini-2.5-flash-image-hd"
DEFAULT_ASPECT = "1:1"
DEFAULT_FORMAT = "png"
DEFAULT_RESOLUTION = "1k"
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_TIMEOUT = 120.0


def get_config_path():
    """Get the path to the config file."""
    config_dir = Path.home() / ".ai-draw"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config():
    """Load configuration from disk, returning defaults if not found."""
    config_path = get_config_path()
    if not config_path.exists():
        return get_default_config()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**get_default_config(), **data}
    except Exception:
        return get_default_config()


def save_config(config):
    """Save configuration to disk."""
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_default_config():
    """Return default configuration."""
    return {
        "api_base": DEFAULT_API_BASE,
        "api_key": os.getenv("GPTSAPI_API_KEY", ""),
        "provider": DEFAULT_PROVIDER,
        "model": DEFAULT_MODEL,
        "aspect": DEFAULT_ASPECT,
        "format": DEFAULT_FORMAT,
        "resolution": DEFAULT_RESOLUTION,
        "poll_interval": DEFAULT_POLL_INTERVAL,
        "timeout": DEFAULT_TIMEOUT,
    }


def get_api_key(config=None):
    """Get API key from config or environment."""
    if config and config.get("api_key"):
        return config["api_key"]
    return os.getenv("GPTSAPI_API_KEY", "")
