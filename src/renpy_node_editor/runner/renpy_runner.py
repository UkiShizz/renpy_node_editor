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


def is_renpy_project(project_dir: Path) -> bool:
    """
    Проверяет, является ли директория проектом Ren'Py.
    
    Args:
        project_dir: Путь к директории для проверки
        
    Returns:
        True если это проект Ren'Py (есть папка game/)
    """
    return (project_dir / "game").is_dir()


def find_existing_labels(game_dir: Path) -> set[str]:
    """
    Находит все существующие метки в проекте Ren'Py.
    
    Args:
        game_dir: Путь к папке game/ проекта Ren'Py
        
    Returns:
        Множество имен существующих меток
    """
    labels: set[str] = set()
    
    if not game_dir.is_dir():
        return labels
    
    # Ищем все .rpy файлы в папке game/
    for rpy_file in game_dir.glob("*.rpy"):
        try:
            with rpy_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Пропускаем комментарии
                    if line.startswith("#"):
                        continue
                    # Ищем строки вида "label имя:" или "label имя:" с пробелами
                    if line.startswith("label "):
                        # Убираем "label " и все после ":"
                        label_part = line[6:].strip()
                        if ":" in label_part:
                            label_name = label_part.split(":")[0].strip()
                            if label_name:
                                labels.add(label_name)
        except Exception:
            # Игнорируем ошибки чтения файлов
            continue
    
    return labels


def export_to_renpy_project(project: Project, project_dir: Path) -> Path:
    """
    Экспортирует проект в существующий или новый проект Ren'Py.
    Если проект уже существует - добавляет сгенерированный код.
    Если проекта нет - создает новый.
    
    Args:
        project: Проект редактора
        project_dir: Директория проекта Ren'Py (корень проекта)
        
    Returns:
        Путь к директории проекта
    """
    # Проверяем, существует ли уже проект Ren'Py
    is_existing = is_renpy_project(project_dir)
    
    # Создаем или используем существующую папку game/
    game_dir = project_dir / "game"
    game_dir.mkdir(parents=True, exist_ok=True)
    
    # Проверяем существующие метки, если проект уже существует
    existing_labels: set[str] = set()
    if is_existing:
        existing_labels = find_existing_labels(game_dir)
    
    # Создаем копию проекта для модификации меток
    from copy import deepcopy
    modified_project = deepcopy(project)
    
    # Изменяем метки сцен, если они конфликтуют с существующими
    for scene in modified_project.scenes:
        original_label = scene.label
        if original_label in existing_labels:
            # Используем уникальное имя: имя_проекта_имя_сцены
            safe_project_name = project.name.replace(" ", "_").replace("-", "_")
            safe_scene_name = scene.name.replace(" ", "_").replace("-", "_")
            new_label = f"{safe_project_name}_{safe_scene_name}"
            
            # Если и это имя занято, добавляем суффикс
            counter = 1
            while new_label in existing_labels:
                new_label = f"{safe_project_name}_{safe_scene_name}_{counter}"
                counter += 1
            
            scene.label = new_label
            existing_labels.add(new_label)  # Добавляем в множество, чтобы избежать конфликтов между сценами
    
    # Генерируем и сохраняем script.rpy
    # Если файл уже существует, создаем новый с уникальным именем
    script_path = game_dir / "script.rpy"
    if script_path.exists() and is_existing:
        # Для существующего проекта создаем файл с именем проекта
        safe_name = project.name.replace(" ", "_").replace("-", "_")
        script_path = game_dir / f"{safe_name}_script.rpy"
    
    code = generate_renpy_script(modified_project)
    with script_path.open("w", encoding="utf-8") as f:
        f.write(code)
    
    # Создаем базовые файлы только для нового проекта
    if not is_existing:
        # Создаем options.rpy с базовыми настройками
        options_path = game_dir / "options.rpy"
        if not options_path.exists():
            options_content = f'''## Имя проекта
define config.name = _("{project.name}")

## Версия проекта
define config.version = "1.0"

## Разрешение экрана
define config.screen_width = 1920
define config.screen_height = 1080

## Полноэкранный режим (по умолчанию выключен)
define config.fullscreen = False

## Автосохранения
define config.has_quicksave = True
define config.has_autosave = True
define config.autosave_frequency = 10

## Звук
define config.has_sound = True
define config.has_music = True
define config.has_voice = True

## Пропуск текста
define config.skip_delay = 0
'''
            with options_path.open("w", encoding="utf-8") as f:
                f.write(options_content)
        
        # Создаем gui.rpy с базовыми настройками GUI (если не существует)
        gui_path = game_dir / "gui.rpy"
        if not gui_path.exists():
            gui_content = '''## GUI настройки
## Эти настройки управляют внешним видом интерфейса игры.

## Цвета
define gui.accent_color = '#4A90E2'
define gui.idle_color = '#888888'
define gui.hover_color = '#4A90E2'
define gui.selected_color = '#FFFFFF'
define gui.insensitive_color = '#8888887f'

## Размеры шрифтов
define gui.text_size = 28
define gui.name_text_size = 36
define gui.interface_text_size = 28
define gui.button_text_size = 28
define gui.label_text_size = 36

## Интерфейс
define gui.textbox_height = 185
define gui.textbox_yalign = 1.0
'''
            with gui_path.open("w", encoding="utf-8") as f:
                f.write(gui_content)
    
    return project_dir


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
