from __future__ import annotations

from typing import Optional
import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QInputDialog, QMessageBox
)
from PySide6.QtGui import QFont, QColor

from renpy_node_editor.core.model import Project, Scene


class SceneManagerPanel(QWidget):
    """
    Панель управления сценами:
    - список сцен
    - создание новой сцены
    - удаление сцены
    - переключение между сценами
    """
    
    # Signal emitted when scene selection changes
    scene_selected = Signal(object)  # emits Scene
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._project: Optional[Project] = None
        self._current_scene: Optional[Scene] = None
        
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 11px;
                padding: 4px;
            }
            QPushButton {
                background-color: #3A3A3A;
                border: 2px solid #4A4A4A;
                border-radius: 6px;
                padding: 6px 12px;
                color: #E0E0E0;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
                border-color: #5A5A5A;
            }
            QPushButton:pressed {
                background-color: #2A2A2A;
            }
            QListWidget {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                color: #E0E0E0;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #3A3A3A;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Заголовок
        title = QLabel("🎬 Сцены")
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        btn_add = QPushButton("➕ Создать", self)
        btn_add.setToolTip("Создать новую сцену в проекте")
        btn_add.clicked.connect(self._on_add_scene)
        buttons_layout.addWidget(btn_add)
        
        btn_delete = QPushButton("➖ Удалить", self)
        btn_delete.setToolTip("Удалить выбранную сцену из проекта")
        btn_delete.clicked.connect(self._on_delete_scene)
        buttons_layout.addWidget(btn_delete)
        
        layout.addLayout(buttons_layout)
        
        # Список сцен
        self.scenes_list = QListWidget(self)
        self.scenes_list.itemDoubleClicked.connect(self._on_scene_double_clicked)
        self.scenes_list.itemSelectionChanged.connect(self._on_scene_selection_changed)
        layout.addWidget(self.scenes_list)
    
    def set_project(self, project: Optional[Project]) -> None:
        """Установить проект и обновить список сцен"""
        self._project = project
        self._refresh_scenes_list()
    
    def set_current_scene(self, scene: Optional[Scene]) -> None:
        """Установить текущую сцену"""
        self._current_scene = scene
        self._refresh_scenes_list()
    
    def _refresh_scenes_list(self) -> None:
        """Обновить список сцен"""
        self.scenes_list.clear()
        
        if not self._project:
            return
        
        for scene in self._project.scenes:
            item_text = f"{scene.name}\n  ({scene.label})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, scene.id)
            
            # Выделяем текущую сцену
            if self._current_scene and scene.id == self._current_scene.id:
                item.setSelected(True)
                item.setForeground(QColor("#4A90E2"))
            
            self.scenes_list.addItem(item)
    
    def _on_add_scene(self) -> None:
        """Создать новую сцену"""
        if not self._project:
            QMessageBox.warning(self, "Нет проекта", "Сначала создайте проект.")
            return
        
        # Запрашиваем имя сцены
        name, ok = QInputDialog.getText(
            self, 
            "Новая сцена", 
            "Имя сцены:",
            text=f"Scene_{len(self._project.scenes) + 1}"
        )
        if not ok or not name:
            return
        
        # Запрашиваем метку (label)
        label, ok = QInputDialog.getText(
            self,
            "Новая сцена",
            "Метка (label) для Ren'Py:",
            text=name.lower().replace(" ", "_")
        )
        if not ok or not label:
            return
        
        # Создаем новую сцену
        scene_id = str(uuid.uuid4())
        new_scene = Scene(
            id=scene_id,
            name=name,
            label=label
        )
        
        self._project.add_scene(new_scene)
        self._refresh_scenes_list()
        
        # Автоматически выбираем новую сцену
        self.scene_selected.emit(new_scene)
    
    def _on_delete_scene(self) -> None:
        """Удалить выбранную сцену"""
        if not self._project:
            return
        
        current_item = self.scenes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Нет выбора", "Выберите сцену для удаления.")
            return
        
        scene_id = current_item.data(Qt.UserRole)
        scene = self._project.find_scene(scene_id)
        
        if not scene:
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Удаление сцены",
            f"Вы уверены, что хотите удалить сцену '{scene.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Нельзя удалить последнюю сцену
            if len(self._project.scenes) <= 1:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Нельзя удалить последнюю сцену в проекте."
                )
                return
            
            self._project.remove_scene(scene_id)
            self._refresh_scenes_list()
            
            # Выбираем первую доступную сцену
            if self._project.scenes:
                self.scene_selected.emit(self._project.scenes[0])
    
    def _on_scene_double_clicked(self, item: QListWidgetItem) -> None:
        """Обработка двойного клика по сцене"""
        scene_id = item.data(Qt.UserRole)
        if not self._project:
            return
        
        scene = self._project.find_scene(scene_id)
        if scene:
            self.scene_selected.emit(scene)
    
    def _on_scene_selection_changed(self) -> None:
        """Обработка изменения выбора сцены"""
        current_item = self.scenes_list.currentItem()
        if not current_item or not self._project:
            return
        
        scene_id = current_item.data(Qt.UserRole)
        scene = self._project.find_scene(scene_id)
        if scene:
            self.scene_selected.emit(scene)
