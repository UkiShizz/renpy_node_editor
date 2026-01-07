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
from PySide6.QtGui import QFont

from renpy_node_editor.app_controller import EditorController
from renpy_node_editor.core.model import Scene
from renpy_node_editor.runner.renpy_env import RenpyEnv, default_env
from renpy_node_editor.runner.renpy_runner import write_project_files, run_project
from renpy_node_editor.ui.block_palette import BlockPalette
from renpy_node_editor.ui.node_graph.node_view import NodeView
from renpy_node_editor.ui.preview_panel import PreviewPanel
from renpy_node_editor.ui.block_properties_panel import BlockPropertiesPanel
from renpy_node_editor.ui.scene_manager_panel import SceneManagerPanel


class MainWindow(QMainWindow):
    """
    Главное окно редактора с современным дизайном:
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
        self.resize(1400, 800)
        
        # Применяем темную тему
        self._apply_style()

        self._build_ui()
        self._update_window_title()

    def _apply_style(self) -> None:
        """Применить современный стиль к окну"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #3A3A3A;
                border: 2px solid #4A4A4A;
                border-radius: 6px;
                padding: 8px 16px;
                color: #E0E0E0;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
                border-color: #5A5A5A;
            }
            QPushButton:pressed {
                background-color: #2A2A2A;
            }
            QLabel {
                color: #E0E0E0;
            }
            QSplitter::handle {
                background-color: #2A2A2A;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
        """)

    # ---- UI ----

    def _build_ui(self) -> None:
        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Верхняя панель кнопок
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        main_layout.addLayout(top_bar)

        btn_new = QPushButton("📁 Новый проект", self)
        btn_new.setToolTip("Создать новый проект визуальной новеллы")
        btn_open = QPushButton("📂 Открыть", self)
        btn_open.setToolTip("Открыть существующий проект")
        btn_save = QPushButton("💾 Сохранить", self)
        btn_save.setToolTip("Сохранить текущий проект")
        btn_generate = QPushButton("⚙️ Сгенерировать код", self)
        btn_generate.setToolTip("Сгенерировать Ren'Py код и показать в панели предпросмотра")
        btn_export = QPushButton("📤 Экспорт в .rpy", self)
        btn_export.setToolTip("Экспортировать сгенерированный код в .rpy файл")
        btn_run = QPushButton("▶️ Запустить в Ren'Py", self)
        btn_run.setToolTip("Запустить проект в Ren'Py SDK")
        btn_center = QPushButton("🎯 Центр", self)
        btn_center.setToolTip("Вернуться в центр рабочей области (0, 0)")

        btn_new.clicked.connect(self._on_new_project)
        btn_open.clicked.connect(self._on_open_project)
        btn_save.clicked.connect(self._on_save_project)
        btn_generate.clicked.connect(self._on_generate_code)
        btn_export.clicked.connect(self._on_export_rpy)
        btn_run.clicked.connect(self._on_run_project)
        btn_center.clicked.connect(self._on_center_view)

        for w in (btn_new, btn_open, btn_save, btn_generate, btn_export, btn_run, btn_center):
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
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        # Панель управления сценами
        self.scene_manager = SceneManagerPanel(self)
        self.scene_manager.scene_selected.connect(self._on_scene_selected)
        right_layout.addWidget(self.scene_manager, 0)

        # Палитра блоков
        palette_label = QLabel("📦 Блоки", self)
        palette_label.setAlignment(Qt.AlignCenter)
        palette_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        palette_label.setFont(palette_font)
        right_layout.addWidget(palette_label)

        self.block_palette = BlockPalette(self)
        right_layout.addWidget(self.block_palette, 1)

        # Превью кода
        self.preview_panel = PreviewPanel(self)
        right_layout.addWidget(self.preview_panel, 1)
        
        # Панель свойств блока
        self.properties_panel = BlockPropertiesPanel(self)
        right_layout.addWidget(self.properties_panel, 1)

        splitter.addWidget(right_container)
        
        # Connect node selection to properties panel (after both are created)
        self.node_view.node_scene.node_selection_changed.connect(
            self.properties_panel.set_block
        )
        # Connect properties saved signal to update node display
        self.properties_panel.properties_saved.connect(self._on_properties_saved)
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

        self.scene_manager.set_project(project)
        self.scene_manager.set_current_scene(scene)
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
        self.scene_manager.set_project(project)
        self.scene_manager.set_current_scene(scene)
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
    
    def _on_export_rpy(self) -> None:
        """Экспортировать сгенерированный код в .rpy файл"""
        if not self._controller.project:
            QMessageBox.warning(
                self,
                "Нет проекта",
                "Сначала создай или открой проект.",
            )
            return
        
        # Предлагаем сохранить в папку проекта по умолчанию
        default_name = f"{self._controller.get_project_name()}_script.rpy"
        default_path = None
        if self._controller.project_path:
            default_path = self._controller.project_path / default_name
        
        # Диалог выбора файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в .rpy файл",
            str(default_path) if default_path else default_name,
            "Ren'Py Script Files (*.rpy);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            self._controller.export_to_rpy(Path(file_path))
            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Код успешно экспортирован в:\n{file_path}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось экспортировать файл:\n{str(e)}",
            )

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
    
    def _on_properties_saved(self, block) -> None:
        """Handle properties saved - update the visual representation"""
        from renpy_node_editor.ui.node_graph.node_item import NodeItem
        
        scene = self.node_view.node_scene
        # Find the NodeItem for this block and update its display
        for item in scene.items():
            if isinstance(item, NodeItem) and item.block.id == block.id:
                item.update_display()
                break
    
    def _on_center_view(self) -> None:
        """Вернуться в центр рабочей области"""
        self.node_view.center_view()
    
    def _on_scene_selected(self, scene: Scene) -> None:
        """Обработка выбора сцены"""
        if not self._controller.project:
            return
        
        self.scene_manager.set_current_scene(scene)
        self.node_view.set_project_and_scene(self._controller.project, scene)
        self.preview_panel.clear()