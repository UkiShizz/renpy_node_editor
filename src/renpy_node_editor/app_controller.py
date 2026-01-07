from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

from renpy_node_editor.core.model import Project
from renpy_node_editor.core.serialization import (
    load_project,
    save_project,
    project_from_dict,
)
from renpy_node_editor.core.generator import generate_renpy_script


@dataclass
class EditorState:
    current_project: Optional[Project] = None
    current_project_path: Optional[Path] = None


class EditorController:
    """
    Контроллер редактора:
    - создаёт/открывает/сохраняет проекты;
    - держит текущий Project в памяти;
    - генерит Ren'Py-код из модели.
    """

    def __init__(self) -> None:
        self._state = EditorState()

    # ---- доступ к состоянию ----

    @property
    def project(self) -> Optional[Project]:
        return self._state.current_project

    @property
    def project_path(self) -> Optional[Path]:
        return self._state.current_project_path

    # ---- операции с проектом ----

    def new_project(self, name: str, directory: Path) -> Project:
        """
        Создать новый проект в указанной папке.

        directory — путь к директории проекта (куда ляжет project.json).
        Шаблон берём из configs/project_template.json и подменяем name.
        """
        directory.mkdir(parents=True, exist_ok=True)

        # ищем шаблон рядом с корнем пакета (renpy_node_editor/../configs)
        root = Path(__file__).resolve().parents[2]  # .../renpy_node_editor/
        template_path = root / "configs" / "project_template.json"

        if template_path.is_file():
            with template_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            payload["name"] = name
            project = project_from_dict(payload)
        else:
            # fallback: пустой проект без сцен
            project = Project(name=name)

        save_project(project, directory)

        self._state.current_project = project
        self._state.current_project_path = directory

        return project

    def open_project(self, directory: Path) -> Project:
        """
        Открыть существующий проект из directory (где лежит project.json).
        """
        project = load_project(directory)

        self._state.current_project = project
        self._state.current_project_path = directory

        return project

    def save_current_project(self) -> None:
        """
        Сохранить текущий проект в его директорию.
        """
        if not self._state.current_project or not self._state.current_project_path:
            return

        save_project(self._state.current_project, self._state.current_project_path)

    # ---- генерация Ren'Py ----

    def generate_script(self) -> str:
        """
        Сгенерировать текст script.rpy для текущего проекта.
        """
        if not self._state.current_project:
            return ""

        return generate_renpy_script(self._state.current_project)
    
    def export_to_rpy(self, file_path: Path) -> None:
        """
        Экспортировать сгенерированный код в .rpy файл.
        
        Args:
            file_path: Путь к файлу для сохранения
        """
        if not self._state.current_project:
            raise ValueError("Нет открытого проекта")
        
        code = generate_renpy_script(self._state.current_project)
        
        # Создаем директорию если нужно
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл
        with file_path.open("w", encoding="utf-8") as f:
            f.write(code)

    # ---- удобняшки ----

    def has_project(self) -> bool:
        return self._state.current_project is not None

    def get_project_name(self) -> str:
        if self._state.current_project:
            return self._state.current_project.name
        return "No project"

    def get_project_dir(self) -> Optional[Path]:
        return self._state.current_project_path
