"""Centralized path resolution for Kodiak.

Handles config, data, and log directories for both development and installed environments.
Uses XDG Base Directory spec on Linux, standard locations on macOS/Windows.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path


def _find_repo_root() -> Path | None:
    """Walk up from this file to find the monorepo root (contains .git)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # safety limit
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def get_config_dir(custom_path: Path | None = None) -> Path:
    """Get the configuration directory path.

    Priority:
    1. Custom path if provided
    2. Development mode: repo root / config (if exists)
    3. Installed mode: ~/.kodiak/config (or XDG_CONFIG_HOME/kodiak on Linux)
    """
    if custom_path:
        config_dir = Path(custom_path)
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    # Check if we're in development mode
    repo_root = _find_repo_root()
    if repo_root:
        dev_config = repo_root / "config"
        if dev_config.exists() and (dev_config / "strategies.yaml").exists():
            return dev_config

    # Installed mode - use user config directory
    system = platform.system()

    if system == "Linux":
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "kodiak"
        else:
            config_dir = Path.home() / ".config" / "kodiak"
    elif system == "Darwin":
        config_dir = Path.home() / ".kodiak" / "config"
    else:
        appdata = os.getenv("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "kodiak" / "config"
        else:
            config_dir = Path.home() / ".kodiak" / "config"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir(custom_path: Path | None = None) -> Path:
    """Get the data directory path.

    Priority:
    1. Custom path if provided
    2. Development mode: repo root / data (if exists)
    3. Installed mode: ~/.kodiak/data (or XDG_DATA_HOME/kodiak on Linux)
    """
    if custom_path:
        data_dir = Path(custom_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    # Check if we're in development mode
    repo_root = _find_repo_root()
    if repo_root:
        dev_data = repo_root / "data"
        if dev_data.exists():
            return dev_data

    # Installed mode - use user data directory
    system = platform.system()

    if system == "Linux":
        xdg_data = os.getenv("XDG_DATA_HOME")
        if xdg_data:
            data_dir = Path(xdg_data) / "kodiak"
        else:
            data_dir = Path.home() / ".local" / "share" / "kodiak"
    elif system == "Darwin":
        data_dir = Path.home() / ".kodiak" / "data"
    else:
        appdata = os.getenv("APPDATA")
        if appdata:
            data_dir = Path(appdata) / "kodiak" / "data"
        else:
            data_dir = Path.home() / ".kodiak" / "data"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir(custom_path: Path | None = None) -> Path:
    """Get the log directory path.

    Priority:
    1. Custom path if provided
    2. Development mode: repo root / logs (if exists)
    3. Installed mode: ~/.kodiak/logs (or XDG_STATE_HOME/kodiak on Linux)
    """
    if custom_path:
        log_dir = Path(custom_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    # Check if we're in development mode
    repo_root = _find_repo_root()
    if repo_root:
        dev_logs = repo_root / "logs"
        if dev_logs.exists():
            return dev_logs

    # Installed mode - use user log directory
    system = platform.system()

    if system == "Linux":
        xdg_state = os.getenv("XDG_STATE_HOME")
        if xdg_state:
            log_dir = Path(xdg_state) / "kodiak"
        else:
            log_dir = Path.home() / ".local" / "state" / "kodiak"
    elif system == "Darwin":
        log_dir = Path.home() / ".kodiak" / "logs"
    else:
        appdata = os.getenv("APPDATA")
        if appdata:
            log_dir = Path(appdata) / "kodiak" / "logs"
        else:
            log_dir = Path.home() / ".kodiak" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_project_root() -> Path:
    """Get the monorepo root directory.

    Walks up from this file looking for .git directory.
    """
    repo_root = _find_repo_root()
    if repo_root:
        return repo_root
    # Fallback: best guess
    return Path(__file__).resolve().parent.parent.parent.parent.parent
