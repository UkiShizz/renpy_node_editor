from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple

from renpy_node_editor.core.model import Project, Block, BlockType
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


def extract_definitions_from_script(script_path: Path) -> str:
    """
    Извлекает определения (define, init, image и т.д.) из существующего script.rpy.
    Возвращает все строки до первой метки label.
    
    Args:
        script_path: Путь к файлу script.rpy
        
    Returns:
        Строка с определениями (define, init, image и т.д.)
    """
    if not script_path.exists():
        return ""
    
    definitions: list[str] = []
    in_label_section = False
    
    try:
        with script_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                
                # Проверяем, начинается ли метка label
                if stripped.startswith("label ") and stripped.endswith(":"):
                    in_label_section = True
                    break
                
                # Если еще не в секции меток, сохраняем строку
                if not in_label_section:
                    definitions.append(line)
    
    except Exception:
        # В случае ошибки возвращаем пустую строку
        return ""
    
    return "".join(definitions)


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


def convert_file_paths_to_relative(project: Project, game_dir: Path) -> None:
    """
    Конвертирует абсолютные пути к файлам в относительные от game/.
    Модифицирует проект in-place. Файлы не копируются.
    """
    def convert_path(old_path: str, default_subdir: str = "") -> str:
        """
        Конвертирует абсолютный путь в относительный от game/.
        
        Args:
            old_path: Исходный путь (может быть абсолютным или относительным)
            default_subdir: Подпапка по умолчанию (images, audio и т.д.)
        
        Returns:
            Относительный путь от game/ с прямыми слешами
        """
        if not old_path:
            return old_path
        
        old_path_str = str(old_path).strip().replace("\\", "/")
        
        # Если путь уже относительный (не абсолютный Windows путь и не Unix абсолютный)
        is_absolute = (len(old_path_str) >= 2 and old_path_str[1] == ":") or old_path_str.startswith("/")
        if not is_absolute:
            return old_path_str
        
        # Это абсолютный путь - ищем "/game/" в пути (регистронезависимо)
        old_path_lower = old_path_str.lower()
        game_marker = "/game/"
        
        if game_marker in old_path_lower:
            # Находим позицию "/game/" в нижнем регистре
            game_pos_lower = old_path_lower.find(game_marker)
            if game_pos_lower != -1:
                # Берем часть после "/game/" из оригинального пути (с учетом регистра)
                relative_part = old_path_str[game_pos_lower + len(game_marker):]
                # Убираем ведущие слеши, если есть
                relative_part = relative_part.lstrip("/")
                if relative_part:  # Если что-то осталось
                    return relative_part
        
        # Также проверяем вариант с обратными слешами
        if "\\game\\" in old_path_lower or "\\game/" in old_path_lower or "/game\\" in old_path_lower:
            # Ищем любой вариант "/game/" или "\game\"
            for marker in ["/game/", "\\game\\", "\\game/", "/game\\"]:
                pos = old_path_lower.find(marker.lower())
                if pos != -1:
                    relative_part = old_path_str[pos + len(marker):]
                    relative_part = relative_part.lstrip("/\\")
                    if relative_part:
                        return relative_part.replace("\\", "/")
        
        # Если не нашли "/game/", пытаемся через Path
        try:
            old_path_obj = Path(old_path)
            game_dir_resolved = game_dir.resolve()
            old_path_resolved = old_path_obj.resolve()
            
            # Пытаемся вычислить относительный путь
            try:
                relative_path = old_path_resolved.relative_to(game_dir_resolved)
                return str(relative_path).replace("\\", "/")
            except ValueError:
                # Путь не находится внутри game_dir
                pass
        except (RuntimeError, OSError):
            pass
        
        # Если ничего не помогло, используем имя файла с подпапкой
        filename = Path(old_path).name
        if default_subdir:
            return f"{default_subdir}/{filename}"
        return filename
    
    # Обрабатываем все блоки в сценах
    for scene in project.scenes:
        for block in scene.blocks:
            # IMAGE блоки
            if block.type == BlockType.IMAGE:
                path = block.params.get("path", "")
                if path:
                    new_path = convert_path(path, "images")
                    block.params["path"] = new_path
            
            # SOUND блоки
            elif block.type == BlockType.SOUND:
                sound_file = block.params.get("sound_file", "")
                if sound_file:
                    new_path = convert_path(sound_file, "audio")
                    block.params["sound_file"] = new_path
            
            # MUSIC блоки
            elif block.type == BlockType.MUSIC:
                music_file = block.params.get("music_file", "")
                if music_file:
                    new_path = convert_path(music_file, "audio")
                    block.params["music_file"] = new_path
            
            # QUEUE_MUSIC блоки
            elif block.type == BlockType.QUEUE_MUSIC:
                music_file = block.params.get("music_file", "")
                if music_file:
                    new_path = convert_path(music_file, "audio")
                    block.params["music_file"] = new_path
            
            # QUEUE_SOUND блоки
            elif block.type == BlockType.QUEUE_SOUND:
                sound_file = block.params.get("sound_file", "")
                if sound_file:
                    new_path = convert_path(sound_file, "audio")
                    block.params["sound_file"] = new_path
            
            # VOICE блоки
            elif block.type == BlockType.VOICE:
                voice_file = block.params.get("voice_file", "")
                if voice_file:
                    new_path = convert_path(voice_file, "audio")
                    block.params["voice_file"] = new_path


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
    
    # Создаем копию проекта для модификации меток и путей
    from copy import deepcopy
    modified_project = deepcopy(project)
    
    # Конвертируем пути к файлам в относительные
    convert_file_paths_to_relative(modified_project, game_dir)
    
    # Изменяем метки сцен, если они конфликтуют с существующими
    # ВАЖНО: метка "start" обязательна для Ren'Py, её нельзя переименовывать!
    has_start_label = "start" in existing_labels
    
    for scene in modified_project.scenes:
        original_label = scene.label
        
        # Если метка "start" и она уже существует в проекте - не переименовываем
        # Если метка "start" и её нет в проекте - оставляем как есть (это будет точка входа)
        if original_label == "start":
            if has_start_label:
                # Если start уже есть, переименовываем нашу сцену
                safe_project_name = project.name.replace(" ", "_").replace("-", "_")
                safe_scene_name = scene.name.replace(" ", "_").replace("-", "_")
                new_label = f"{safe_project_name}_{safe_scene_name}"
                
                counter = 1
                while new_label in existing_labels:
                    new_label = f"{safe_project_name}_{safe_scene_name}_{counter}"
                    counter += 1
                
                scene.label = new_label
                existing_labels.add(new_label)
            # Если start нет - оставляем как есть, это будет точка входа
            continue
        
        # Для остальных меток - переименовываем при конфликте
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
    
    # Генерируем и сохраняем код
    script_path = game_dir / "script.rpy"
    
    # Генерируем новый код
    generated_code = generate_renpy_script(modified_project)
    
    # Заменяем script.rpy на сгенерированный код
    with script_path.open("w", encoding="utf-8") as f:
        f.write(generated_code)
    
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
