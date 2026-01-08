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
from renpy_node_editor.core.model import Scene, Project
from renpy_node_editor.ui.block_palette import BlockPalette
from renpy_node_editor.ui.node_graph.node_view import NodeView
from renpy_node_editor.ui.preview_panel import PreviewPanel
from renpy_node_editor.ui.block_properties_panel import BlockPropertiesPanel
from renpy_node_editor.ui.scene_manager_panel import SceneManagerPanel
from renpy_node_editor.core.settings import get_splitter_sizes, save_splitter_sizes


class MainWindow(QMainWindow):
    """
    Главное окно редактора с современным дизайном:
    - слева: панель предпросмотра кода (скрываемая)
    - центр: нод-редактор (NodeView/NodeScene)
    - справа: палитра блоков, управление сценами и свойства блоков
    - сверху: кнопки управления проектом
    """

    def __init__(self) -> None:
        super().__init__()

        self._controller = EditorController()

        self.setWindowTitle("RenPy Node Editor")
        self.resize(1400, 800)
        
        # Применяем темную тему
        self._apply_style()

        self._build_ui()
        self._create_default_project()
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
        btn_export = QPushButton("📤 Экспорт в Ren'Py", self)
        btn_export.setToolTip("Экспортировать проект в готовый проект Ren'Py (папку)")
        btn_center = QPushButton("🎯 Центр", self)
        btn_center.setToolTip("Вернуться в центр рабочей области (0, 0)")
        self.btn_toggle_preview = QPushButton("📄 Код", self)
        self.btn_toggle_preview.setToolTip("Показать/скрыть панель предпросмотра кода")
        self.btn_toggle_preview.setCheckable(True)
        self.btn_toggle_preview.setChecked(False)

        btn_new.clicked.connect(self._on_new_project)
        btn_open.clicked.connect(self._on_open_project)
        btn_save.clicked.connect(self._on_save_project)
        btn_generate.clicked.connect(self._on_generate_code)
        btn_export.clicked.connect(self._on_export_rpy)
        btn_center.clicked.connect(self._on_center_view)
        self.btn_toggle_preview.toggled.connect(self._on_toggle_preview)

        # Кнопка просмотра кода слева, остальные справа
        top_bar.addWidget(self.btn_toggle_preview)
        for w in (btn_new, btn_open, btn_save, btn_generate, btn_export, btn_center):
            top_bar.addWidget(w)
        top_bar.addStretch(1)

        # Центральный сплиттер: слева превью кода, центр ноды, справа палитра
        self.main_splitter = QSplitter(Qt.Horizontal, self)
        main_layout.addWidget(self.main_splitter, 1)

        # Превью кода (слева, по умолчанию скрыто)
        self.preview_panel = PreviewPanel(self)
        self.main_splitter.addWidget(self.preview_panel)
        self.preview_panel.setVisible(False)  # По умолчанию скрыто

        # Нод-редактор (в центре)
        self.node_view = NodeView(self)
        self.main_splitter.addWidget(self.node_view)

        # Правая часть — палитра блоков, управление сценами и свойства
        right_container = QWidget(self)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(0)

        # Вертикальный сплиттер для всех панелей справа
        self.right_splitter = QSplitter(Qt.Vertical, self)
        right_layout.addWidget(self.right_splitter, 1)

        # Панель управления сценами
        self.scene_manager = SceneManagerPanel(self)
        self.scene_manager.scene_selected.connect(self._on_scene_selected)
        self.right_splitter.addWidget(self.scene_manager)

        # Палитра блоков
        palette_label = QLabel("📦 Блоки", self)
        palette_label.setAlignment(Qt.AlignCenter)
        palette_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        palette_label.setFont(palette_font)
        
        self.block_palette = BlockPalette(self)
        
        palette_container = QWidget(self)
        palette_layout = QVBoxLayout(palette_container)
        palette_layout.setContentsMargins(0, 0, 0, 0)
        palette_layout.setSpacing(0)
        palette_layout.addWidget(palette_label)
        palette_layout.addWidget(self.block_palette)
        
        self.right_splitter.addWidget(palette_container)
        
        # Панель свойств блока
        self.properties_panel = BlockPropertiesPanel(self)
        self.right_splitter.addWidget(self.properties_panel)

        self.main_splitter.addWidget(right_container)
        
        # Connect properties saved signal to update node display
        self.properties_panel.properties_saved.connect(self._on_properties_saved)
        
        # Загружаем сохраненные пропорции
        self._load_splitter_sizes()
        
        # Сохраняем пропорции при изменении
        self.main_splitter.splitterMoved.connect(
            lambda pos, index: self._on_splitter_moved("main", pos, index)
        )
        self.right_splitter.splitterMoved.connect(
            lambda pos, index: self._on_splitter_moved("right", pos, index)
        )

        self.setCentralWidget(central)
        
        # Теперь подключаем сигналы после установки центрального виджета
        self._connect_scene_signals()
    
    def _connect_scene_signals(self) -> None:
        """Подключить сигналы сцены к панели свойств"""
        try:
            scene = self.node_view.node_scene
            if not scene:
                return
            # Отключаем ВСЕ старые соединения если есть
            try:
                if scene.receivers(scene.node_selection_changed) > 0:
                    scene.node_selection_changed.disconnect()
            except (TypeError, RuntimeError):
                pass
            # Подключаем новые
            scene.node_selection_changed.connect(
                self.properties_panel.set_block
            )
        except Exception:
            pass
    
    def _create_default_scene_if_needed(self, project: Project) -> Scene:
        """Создать базовую сцену, если в проекте нет сцен"""
        import uuid
        if not project.scenes:
            scene = Scene(id=str(uuid.uuid4()), name="Main Scene", label="start")
            project.add_scene(scene)
            # Не сохраняем при создании - сохраним при первом сохранении пользователем
            return scene
        return project.scenes[0]
    
    def _create_default_project(self) -> None:
        """Создать новый чистый проект при старте (без сохранения)"""
        # Создаем проект только в памяти, без сохранения
        # При первом сохранении пользователь выберет папку
        from renpy_node_editor.core.model import Project
        import uuid
        
        project = Project(name="New Project")
        scene = self._create_default_scene_if_needed(project)
        
        # Устанавливаем проект в контроллере, но БЕЗ пути (будет запрошен при сохранении)
        self._controller._state.current_project = project
        self._controller._state.current_project_path = None
        
        # Загружаем проект в UI
        self._load_project(project, scene)
    
    def _load_project(self, project: Project, scene: Scene) -> None:
        """Загрузить проект и сцену в UI"""
        try:
            self.scene_manager.set_project(project)
            self.scene_manager.set_current_scene(scene)
            self.node_view.set_project_and_scene(project, scene)
            
            # Переподключаем сигналы сразу после установки сцены
            self._connect_scene_signals()
            
            self.preview_panel.clear()
            self._update_window_title()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки проекта",
                f"Не удалось загрузить проект:\n{str(e)}"
            )

    def _update_window_title(self) -> None:
        name = self._controller.get_project_name()
        self.setWindowTitle(f"RenPy Node Editor - {name}")

    # ---- слоты верхних кнопок ----

    def _on_new_project(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Имя проекта", "Имя проекта:")
        if not ok or not name:
            return

        # Создаем проект только в памяти, без сохранения
        # Папка будет запрошена при первом сохранении
        from renpy_node_editor.core.model import Project
        import uuid
        
        project = Project(name=name)
        scene = self._create_default_scene_if_needed(project)
        
        # Устанавливаем проект в контроллере, но БЕЗ пути (будет запрошен при сохранении)
        self._controller._state.current_project = project
        self._controller._state.current_project_path = None
        
        self._load_project(project, scene)

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
        if not self._controller.project:
            QMessageBox.warning(
                self,
                "Нет проекта",
                "Сначала создай или открой проект.",
            )
            return
        
        # Если проект еще не был сохранен, предлагаем выбрать папку
        if not self._controller.project_path:
            base_dir = QFileDialog.getExistingDirectory(
                self,
                "Выбери папку для сохранения проекта",
            )
            if not base_dir:
                return
            
            # Спрашиваем имя проекта, если нужно
            project_name = self._controller.project.name if self._controller.project else "New Project"
            project_dir = Path(base_dir) / project_name
            
            # Если папка уже существует, спрашиваем подтверждение
            if project_dir.exists():
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Папка существует",
                    f"Папка {project_dir} уже существует. Перезаписать?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Сохраняем проект в выбранную папку
            from renpy_node_editor.core.serialization import save_project
            save_project(self._controller.project, project_dir)
            # Обновляем путь в контроллере
            if hasattr(self._controller, '_state'):
                self._controller._state.current_project_path = project_dir
            self._update_window_title()
        else:
            # Проект уже имеет путь - сохраняем туда
            self._controller.save_current_project()
        
        # Показываем сообщение с путем
        project_path = self._controller.project_path
        if project_path:
            QMessageBox.information(
                self,
                "Сохранено",
                f"Проект сохранён в:\n{project_path}\n\nФайл: {project_path / 'project.json'}",
            )
        else:
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
        # Показываем панель предпросмотра, если она скрыта
        if not self.preview_panel.isVisible():
            self.btn_toggle_preview.setChecked(True)
            self._on_toggle_preview(True)
    
    def _on_export_rpy(self) -> None:
        """Экспортировать проект в готовый проект Ren'Py"""
        if not self._controller.project:
            QMessageBox.warning(
                self,
                "Нет проекта",
                "Сначала создай или открой проект.",
            )
            return
        
        # Предлагаем путь к существующему проекту Ren'Py по умолчанию
        default_path = Path("C:\\Users\\ukish\\Desktop\\Новая папка")
        if not default_path.exists():
            # Если стандартный путь не существует, предлагаем рядом с текущим проектом
            if self._controller.project_path:
                default_path = self._controller.project_path.parent / f"{self._controller.get_project_name()}_renpy"
            else:
                default_path = Path.home() / f"{self._controller.get_project_name()}_renpy"
        
        # Диалог выбора папки
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Экспорт в проект Ren'Py - выберите папку проекта",
            str(default_path),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not project_dir:
            return
        
        project_path = Path(project_dir)
        
        # Проверяем, является ли это существующим проектом Ren'Py
        from renpy_node_editor.runner.renpy_runner import is_renpy_project
        is_existing = is_renpy_project(project_path)
        
        if is_existing:
            # Для существующего проекта объединяем с script.rpy
            script_path = project_path / "game" / "script.rpy"
            if script_path.exists():
                reply = QMessageBox.question(
                    self,
                    "Экспорт в существующий проект",
                    f"Выбран существующий проект Ren'Py:\n{project_dir}\n\n"
                    f"⚠️ ВНИМАНИЕ: Файл script.rpy будет полностью заменен!\n"
                    f"Текущее содержимое script.rpy будет потеряно.\n\n"
                    f"✅ Будет создан новый script.rpy со сгенерированным кодом.\n"
                    f"✅ Другие файлы (options.rpy, gui.rpy и т.д.) не будут изменены.\n\n"
                    f"Продолжить?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            else:
                # Если script.rpy нет, создаем его
                reply = QMessageBox.question(
                    self,
                    "Экспорт в существующий проект",
                    f"Выбран существующий проект Ren'Py:\n{project_dir}\n\n"
                    f"Сгенерированный код будет сохранен в game/script.rpy.\n\n"
                    f"Продолжить?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.No:
                    return
        elif project_path.exists() and any(project_path.iterdir()):
            # Для новой папки предупреждаем, если она не пуста
            reply = QMessageBox.question(
                self,
                "Папка не пуста",
                f"Папка '{project_dir}' не пуста.\n"
                "Будет создан новый проект Ren'Py.\n\n"
                "Продолжить?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        try:
            created_path = self._controller.export_to_renpy_project(project_path)
            
            if is_existing:
                script_path = created_path / "game" / "script.rpy"
                message = (
                    f"Код успешно экспортирован в проект Ren'Py:\n{created_path}\n\n"
                    f"✅ Файл script.rpy заменен:\n{script_path}\n\n"
                    f"✅ Создан новый script.rpy со сгенерированным кодом"
                )
            else:
                message = (
                    f"Проект Ren'Py успешно создан в:\n{created_path}\n\n"
                    f"Структура:\n"
                    f"  {created_path}/\n"
                    f"    game/\n"
                    f"      script.rpy\n"
                    f"      options.rpy\n"
                    f"      gui.rpy"
                )
            
            QMessageBox.information(
                self,
                "Экспорт завершен",
                message,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось экспортировать проект:\n{str(e)}",
            )

    def _on_toggle_preview(self, checked: bool) -> None:
        """Показать/скрыть панель предпросмотра кода"""
        self.preview_panel.setVisible(checked)
        
        if checked:
            # Показываем панель и устанавливаем пропорции
            sizes = self.main_splitter.sizes()
            if len(sizes) >= 3 and sizes[0] == 0:
                # Если превью было скрыто, устанавливаем пропорции для превью:ноды:палитра
                total = sum(sizes) if sum(sizes) > 0 else 1200
                self.main_splitter.setSizes([total // 4, total * 2 // 4, total // 4])
            elif len(sizes) == 2:
                # Если только ноды и палитра, добавляем превью
                total = sum(sizes) if sum(sizes) > 0 else 1200
                self.main_splitter.setSizes([total // 4, total * 2 // 4, total // 4])
        else:
            # Скрываем панель, отдаём всё пространство нодам и палитре
            sizes = self.main_splitter.sizes()
            if len(sizes) >= 3:
                # Перераспределяем пространство между нодами и палитрой
                node_size = sizes[1] + sizes[0] // 2
                palette_size = sizes[2] + sizes[0] // 2
                self.main_splitter.setSizes([0, node_size, palette_size])
    
    def _on_properties_saved(self, block) -> None:
        """Handle properties saved - update the visual representation"""
        if not block:
            return
        
        try:
            from renpy_node_editor.ui.node_graph.node_item import NodeItem
            
            scene = self.node_view.node_scene
            if not scene or not scene._scene_model:
                return
            
            # Проверяем, что блок еще существует в текущей сцене
            if not scene._scene_model.find_block(block.id):
                return
            
            # Find the NodeItem for this block and update its display
            for item in scene.items():
                if isinstance(item, NodeItem):
                    # Проверяем, что элемент еще в сцене
                    if not item.scene():
                        continue
                    if item.block.id == block.id:
                        item.update_display()
                        break
        except Exception:
            pass
    
    def _on_center_view(self) -> None:
        """Вернуться в центр рабочей области"""
        self.node_view.center_view()
    
    def _on_scene_selected(self, scene: Scene) -> None:
        """Обработка выбора сцены"""
        if not self._controller.project:
            return
        
        # Проверяем, что сцена существует в проекте
        found_scene = self._controller.project.find_scene(scene.id)
        if not found_scene:
            return
        scene = found_scene
        
        # Проверяем, что это не та же сцена (избегаем лишних перезагрузок)
        if (self.node_view.node_scene._scene_model and
            self.node_view.node_scene._scene_model.id == scene.id):
            return  # Уже загружена эта сцена
        
        try:
            self._load_project(self._controller.project, scene)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки сцены",
                f"Не удалось загрузить сцену '{scene.name}':\n{str(e)}"
            )
    
    def _load_splitter_sizes(self) -> None:
        """Загрузить сохраненные пропорции панелей"""
        # Загружаем пропорции главного splitter (превью-ноды-палитра)
        saved_sizes = get_splitter_sizes("main")
        if saved_sizes and len(saved_sizes) == 3 and all(s >= 0 for s in saved_sizes):
            self.main_splitter.setSizes(saved_sizes)
        else:
            # По умолчанию: превью скрыто (0), ноды занимают больше места
            # Используем stretch factors для правильного распределения
            self.main_splitter.setStretchFactor(0, 0)  # Превью скрыто
            self.main_splitter.setStretchFactor(1, 3)  # Ноды
            self.main_splitter.setStretchFactor(2, 2)  # Палитра
            # Устанавливаем размеры после показа окна (через небольшой таймаут)
            # Но для начала просто устанавливаем минимальные размеры
            total_width = self.width() if self.width() > 0 else 1400
            self.main_splitter.setSizes([0, int(total_width * 0.6), int(total_width * 0.4)])
        
        # Загружаем пропорции правого splitter (сцены-палитра-свойства)
        saved_right_sizes = get_splitter_sizes("right")
        if saved_right_sizes and len(saved_right_sizes) == 3 and all(s > 0 for s in saved_right_sizes):
            self.right_splitter.setSizes(saved_right_sizes)
        else:
            # Значения по умолчанию (сцены меньше, остальные равномерно)
            for i, factor in enumerate((1, 2, 2)):
                self.right_splitter.setStretchFactor(i, factor)
    
    def _on_splitter_moved(self, splitter_name: str, pos: int, index: int) -> None:
        """Обработчик изменения пропорций панелей"""
        if splitter_name == "main":
            sizes = self.main_splitter.sizes()
            if sizes and len(sizes) == 3:
                save_splitter_sizes(sizes, "main")
        elif splitter_name == "right":
            sizes = self.right_splitter.sizes()
            if sizes and len(sizes) == 3:
                save_splitter_sizes(sizes, "right")