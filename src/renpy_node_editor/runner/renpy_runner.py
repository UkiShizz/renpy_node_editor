from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple

from renpy_node_editor.core.model import Project
from renpy_node_editor.core.generator import generate_renpy_script
from renpy_node_editor.runner.renpy_env import RenpyEnv


def write_project_files(project: Project, project_dir: Path) -> Path:
    """
    Записывает сгенерированный script.rpy в папку Ren'Py-проекта.
    Возвращает путь к script.rpy.
    """
    game_dir = project_dir / "game"
    game_dir.mkdir(parents=True, exist_ok=True)

    script_path = game_dir / "script.rpy"
    code = generate_renpy_script(project)

    with script_path.open("w", encoding="utf-8") as f:
        f.write(code)

    return script_path


def build_run_command(env: RenpyEnv, project_dir: Path) -> Tuple[str, str, str]:
    """
    Собирает команду для запуска:
    python.exe renpy.py <base> run
    """
    python_exe = str(env.python_executable)
    renpy_py = str(env.renpy_py)
    base = str(project_dir.resolve())

    return python_exe, renpy_py, base


def run_project(env: RenpyEnv, project_dir: Path) -> None:
    """
    Запускает Ren'Py проект через SDK, не дожидаясь завершения.
    """
    if not env.is_valid():
        raise RuntimeError(f"Некорректный путь к Ren'Py SDK: {env.sdk_root}")

    python_exe, renpy_py, base = build_run_command(env, project_dir)

    cmd = [python_exe, renpy_py, base, "run"]

    try:
        subprocess.Popen(cmd, cwd=str(env.sdk_root))
    except Exception as exc:
        raise RuntimeError(f"Не удалось запустить Ren'Py: {exc}") from exc
