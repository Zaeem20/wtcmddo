"""Configuration management for wtcmddo."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
CONFIG_DIR = Path.home() / ".wtcmddo"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_config(
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
) -> None:
    """Save configuration to file."""
    _ensure_config_dir()
    config = {"api_key": api_key, "base_url": base_url, "model": model}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_config() -> dict[str, str]:
    """Load configuration from file. Returns defaults if not found."""
    if not CONFIG_FILE.exists():
        return {
            "api_key": "",
            "base_url": DEFAULT_BASE_URL,
            "model": DEFAULT_MODEL,
        }
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "api_key": "",
            "base_url": DEFAULT_BASE_URL,
            "model": DEFAULT_MODEL,
        }


def get_api_key() -> Optional[str]:
    """Get API key from config or environment variable."""
    config = load_config()
    if config["api_key"]:
        return config["api_key"]
    return os.environ.get("OPENROUTER_API_KEY")


def get_config() -> dict[str, str]:
    """Get current configuration."""
    config = load_config()
    return {
        "api_key": config["api_key"] or "(not set)",
        "base_url": config["base_url"],
        "model": config["model"],
    }