"""Settings management for the editor"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

SETTINGS_FILE = "editor_config.json"


def get_settings_path() -> Path:
    """Get path to settings file in the same directory as the executable/script"""
    # Если запущено как скомпилированный exe (PyInstaller)
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        # Если запущено как скрипт Python
        # Находим корень проекта (где находится app.py)
        # app.py находится в src/renpy_node_editor/, поэтому идем на 2 уровня вверх
        _this_file = Path(__file__).resolve()
        # __file__ = .../src/renpy_node_editor/core/settings.py
        # parents[2] = .../renpy_node_editor (корень проекта)
        base_path = _this_file.parents[2]
    
    return base_path / SETTINGS_FILE


def load_settings() -> Dict[str, Any]:
    """Load settings from file. If file is corrupted, create a new one."""
    settings_path = get_settings_path()
    
    if not settings_path.exists():
        # Создаем файл с настройками по умолчанию
        default_settings = _get_default_settings()
        save_settings(default_settings)
        return default_settings
    
    try:
        with settings_path.open("r", encoding="utf-8") as f:
            settings = json.load(f)
            # Валидация: проверяем, что это словарь
            if not isinstance(settings, dict):
                raise ValueError("Settings file is not a valid dictionary")
            return settings
    except (json.JSONDecodeError, IOError, ValueError) as e:
        # Если файл поврежден, создаем новый с настройками по умолчанию
        print(f"Warning: Config file is corrupted ({e}). Creating a new one.")
        default_settings = _get_default_settings()
        save_settings(default_settings)
        return default_settings


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to file"""
    settings_path = get_settings_path()
    
    try:
        # Создаем директорию, если её нет
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем во временный файл, затем переименовываем (атомарная операция)
        temp_path = settings_path.with_suffix('.tmp')
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        # Атомарно заменяем старый файл новым
        if settings_path.exists():
            settings_path.unlink()
        temp_path.rename(settings_path)
    except IOError as e:
        print(f"Error saving config file: {e}")


def get_splitter_sizes(splitter_name: str = "main") -> Optional[list[int]]:
    """Get saved splitter sizes"""
    settings = load_settings()
    # Поддержка старого формата (splitter_sizes_main) и нового (splitter_sizes_{name})
    key = f"splitter_sizes_{splitter_name}"
    return settings.get(key)


def save_splitter_sizes(sizes: list[int], splitter_name: str = "main") -> None:
    """Save splitter sizes"""
    settings = load_settings()
    settings[f"splitter_sizes_{splitter_name}"] = sizes
    save_settings(settings)


def get_renpy_sdk_path() -> Optional[Path]:
    """Get saved Ren'Py SDK path"""
    settings = load_settings()
    path_str = settings.get("renpy_sdk_path")
    if path_str:
        return Path(path_str)
    return None


def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value by key"""
    settings = load_settings()
    return settings.get(key, default)


def _get_default_settings() -> Dict[str, Any]:
    """Get default settings dictionary"""
    return {
        "window_width": 1400,
        "window_height": 800,
        "window_x": None,  # None означает центрирование
        "window_y": None,
        "splitter_sizes_main": [0, 840, 560],  # preview, nodes, palette
        "splitter_sizes_right": [200, 300, 300],  # scenes, palette, properties
        "preview_panel_visible": False,
        "language": "en",
        "show_grid": True,
        "grid_size": 20,
        "show_tooltips": True,
        "auto_center_on_load": True,
    }