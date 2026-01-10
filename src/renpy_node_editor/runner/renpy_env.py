from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from renpy_node_editor.core.settings import get_renpy_sdk_path


@dataclass
class RenpyEnv:
    """
    Окружение Ren'Py SDK.

    sdk_root — корень распакованного SDK, где лежат:
      - renpy.py
      - lib/py3-windows-x86_64/python.exe (на винде)
    """
    sdk_root: Path

    @property
    def renpy_py(self) -> Path:
        return self.sdk_root / "renpy.py"

    @property
    def python_executable(self) -> Path:
        return self.sdk_root / "lib" / "py3-windows-x86_64" / "python.exe"

    def is_valid(self) -> bool:
        return self.renpy_py.is_file() and self.python_executable.is_file()


def default_sdk_root() -> Path:
    """
    Дефолтное место для Ren'Py SDK под Windows:

    C:\\RenPy\\renpy-8.3.7

    Кладёшь туда распакованный SDK (как его выдаёт оф. инсталлятор),
    либо меняешь путь под себя.
    
    Сначала проверяет сохраненный путь из настроек.
    """
    saved_path = get_renpy_sdk_path()
    if saved_path:
        return saved_path
    return Path(r"C:\RenPy\renpy-8.3.7")


def default_env() -> Optional[RenpyEnv]:
    """
    Вернуть RenpyEnv для дефолтного пути, если там реально лежит SDK.
    """
    root = default_sdk_root()
    env = RenpyEnv(sdk_root=root)
    return env if env.is_valid() else None
