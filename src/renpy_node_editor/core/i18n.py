"""Internationalization (i18n) support for the editor"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from renpy_node_editor.core.settings import get_setting

# Default language
DEFAULT_LANGUAGE = "en"

# Translation cache
_translations: Dict[str, Dict[str, str]] = {}
_current_language = DEFAULT_LANGUAGE


def get_language() -> str:
    """Get current language from settings"""
    return get_setting("language", DEFAULT_LANGUAGE)


def set_language(lang: str) -> None:
    """Set current language"""
    global _current_language
    _current_language = lang


def _load_translations() -> Dict[str, Dict[str, str]]:
    """Load all translation files"""
    translations = {}
    
    # Get the directory where this file is located
    i18n_dir = Path(__file__).parent / "i18n"
    
    # Load all JSON files in i18n directory
    for lang_file in i18n_dir.glob("*.json"):
        lang_code = lang_file.stem
        try:
            with lang_file.open("r", encoding="utf-8") as f:
                translations[lang_code] = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue
    
    return translations


def _get_translations() -> Dict[str, Dict[str, str]]:
    """Get translations, loading if necessary"""
    global _translations
    if not _translations:
        _translations = _load_translations()
    return _translations


def tr(key: str, default: str = "") -> str:
    """
    Translate a key to the current language.
    
    Args:
        key: Translation key (e.g., "ui.main_window.title")
        default: Default value if translation not found
    
    Returns:
        Translated string
    """
    lang = get_language()
    translations = _get_translations()
    
    # Try current language
    if lang in translations:
        value = translations[lang].get(key)
        if value:
            return value
    
    # Try default language
    if DEFAULT_LANGUAGE in translations:
        value = translations[DEFAULT_LANGUAGE].get(key)
        if value:
            return value
    
    # Return default or key if no translation found
    return default or key


def reload_translations() -> None:
    """Reload translation files (useful for testing)"""
    global _translations
    _translations = {}
    _load_translations()
