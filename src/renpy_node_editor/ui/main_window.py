from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QSplitter,
    QPushButton,
    QMessageBox,
    QLabel,
)

from renpy_node_editor.app_controller import EditorController
from renpy_node_editor.core.model import Scene
from renpy_node_editor.runner.renpy_env import RenpyEnv, default_env
from renpy_node_editor.runner.renpy_runner import write_project_files, run_project
from renpy_node_editor.ui.block_palette import BlockPalette
from renpy_node_editor.ui.node_graph.node_view import NodeView
from renpy_node_editor.ui.preview_panel import PreviewPanel
from renpy_node_editor.ui.block_properties_panel import BlockPropertiesPanel


class MainWindow(QMainWindow):
    """
    Главное окно редактора:
    - слева: нод-редактор (NodeView/NodeScene)
    - справа: палитра блоков + панель превью кода
    - сверху: кнопки управления проектом
    """

    def __init__(self) -> None:
        super().__init__()

        self._controller = EditorController()
        # пробуем автодетект SDK, если не найдёт — кнопка запуска будет ругаться
        self._renpy_env: Optional[RenpyEnv] = default_env()

        self.setWindowTitle("RenPy Node Editor")
        self.resize(1200, 700)

        self._build_ui()
        self._update_window_title()

    # ---- UI ----

    def _build_ui(self) -> None:
        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Верхняя панель кнопок
        top_bar = QHBoxLayout()
        main_layout.addLayout(top_bar)

        btn_new = QPushButton("Новый проект", self)
        btn_open = QPushButton("Открыть", self)
        btn_save = QPushButton("Сохранить", self)
        btn_generate = QPushButton("Сгенерировать код", self)
        btn_run = QPushButton("Запустить в Ren'Py", self)

        btn_new.clicked.connect(self._on_new_project)
        btn_open.clicked.connect(self._on_open_project)
        btn_save.clicked.connect(self._on_save_project)
        btn_generate.clicked.connect(self._on_generate_code)
        btn_run.clicked.connect(self._on_run_project)

        for w in (btn_new, btn_open, btn_save, btn_generate, btn_run):
            top_bar.addWidget(w)
        top_bar.addStretch(1)

        # Центральный сплиттер: слева ноды, справа палитра+код
        splitter = QSplitter(Qt.Horizontal, self)
        main_layout.addWidget(splitter, 1)

        # Левая часть — нод-редактор
        left_container = QWidget(self)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.node_view = NodeView(self)
        left_layout.addWidget(self.node_view)

        splitter.addWidget(left_container)

        # Правая часть — палитра + превью кода
        right_container = QWidget(self)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(4)

        # Палитра блоков
        palette_label = QLabel("Блоки", self)
        palette_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(palette_label)

        self.block_palette = BlockPalette(self)
        right_layout.addWidget(self.block_palette, 1)

        # Превью кода (PreviewPanel вместо QTextEdit)
        self.preview_panel = PreviewPanel(self)
        right_layout.addWidget(self.preview_panel, 1)
        
        # Панель свойств блока (BlockPropertiesPanel)
        self.properties_panel = BlockPropertiesPanel(self)
        right_layout.addWidget(self.properties_panel, 1)

        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.setCentralWidget(central)

    def _update_window_title(self) -> None:
        name = self._controller.get_project_name()
        self.setWindowTitle(f"RenPy Node Editor - {name}")

    # ---- слоты верхних кнопок ----

    def _on_new_project(self) -> None:
        base_dir = QFileDialog.getExistingDirectory(
            self,
            "Выбери папку для проекта",
        )
        if not base_dir:
            return

        # getText в PySide6 живёт в QInputDialog, но ради простоты можно сделать отдельный диалог позже
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Имя проекта", "Имя проекта:")
        if not ok or not name:
            return

        project_dir = Path(base_dir) / name
        project = self._controller.new_project(name, project_dir)

        # Если в шаблоне нет сцен — создаём базовую
        if not project.scenes:
            scene = Scene(id="scene_1", name="Main Scene", label="start")
            project.add_scene(scene)
        else:
            scene = project.scenes[0]

        self.node_view.set_project_and_scene(project, scene)
        self.preview_panel.clear()
        self._update_window_title()

    def _on_open_project(self) -> None:
        base_dir = QFileDialog.getExistingDirectory(
            self,
            "Выбери папку существующего проекта (где лежит project.json)",
        )
        if not base_dir:
            return

        project_dir = Path(base_dir)
        try:
            self._controller.open_project(project_dir)
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Ошибка",
                "В выбранной папке нет project.json",
            )
            return

        project = self._controller.project
        if not project or not project.scenes:
            QMessageBox.warning(
                self,
                "Ошибка",
                "В проекте нет сцен.",
            )
            return

        scene = project.scenes[0]  # пока просто первая
        self.node_view.set_project_and_scene(project, scene)
        self.preview_panel.clear()
        self._update_window_title()

    def _on_save_project(self) -> None:
        self._controller.save_current_project()
        QMessageBox.information(self, "Сохранено", "Проект сохранён.")

    def _on_generate_code(self) -> None:
        code = self._controller.generate_script()
        if not code:
            QMessageBox.warning(
                self,
                "Нет проекта",
                "Сначала создай или открой проект.",
            )
            return

        self.preview_panel.set_code(code)

    def _on_run_project(self) -> None:
        if not self._controller.project or not self._controller.project_path:
            QMessageBox.warning(
                self,
                "Нет проекта",
                "Сначала создай или открой проект.",
            )
            return

        if self._renpy_env is None or not self._renpy_env.is_valid():
            QMessageBox.warning(
                self,
                "Ren'Py SDK",
                "Не настроен путь к Ren'Py SDK. "
                "По умолчанию ищется C:\\RenPy\\renpy-8.3.7. "
                "Поправь default_sdk_root() в runner/renpy_env.py или _renpy_env в MainWindow.",
            )
            return

        project_dir = self._controller.project_path
        project = self._controller.project

        script_path = write_project_files(project, project_dir)
        try:
            run_project(self._renpy_env, project_dir)
        except RuntimeError as exc:
            QMessageBox.critical(self, "Ошибка запуска", str(exc))
            return

        QMessageBox.information(
            self,
            "Запуск",
            f"Игра запущена через Ren'Py.\nscript.rpy: {script_path}",
        )

