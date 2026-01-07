"""Settings management for the editor"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, Any

SETTINGS_FILE = "editor_settings.json"


def get_settings_path() -> Path:
    """Get path to settings file in user's home directory"""
    home = Path.home()
    settings_dir = home / ".renpy_node_editor"
    settings_dir.mkdir(exist_ok=True)
    return settings_dir / SETTINGS_FILE


def load_settings() -> Dict[str, Any]:
    """Load settings from file"""
    settings_path = get_settings_path()
    
    if not settings_path.exists():
        return {}
    
    try:
        with settings_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to file"""
    settings_path = get_settings_path()
    
    try:
        with settings_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except IOError:
        pass  # Ignore save errors


def get_splitter_sizes(splitter_name: str = "main") -> Optional[list[int]]:
    """Get saved splitter sizes"""
    settings = load_settings()
    return settings.get(f"splitter_sizes_{splitter_name}")


def save_splitter_sizes(sizes: list[int], splitter_name: str = "main") -> None:
    """Save splitter sizes"""
    settings = load_settings()
    settings[f"splitter_sizes_{splitter_name}"] = sizes
    save_settings(settings)
