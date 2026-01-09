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
        self._is_updating_selection = False  # Флаг для предотвращения рекурсивных вызовов
        
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
        
        # Кнопки для изменения порядка сцен
        btn_up = QPushButton("⬆️", self)
        btn_up.setToolTip("Переместить сцену вверх (раньше в порядке генерации)")
        btn_up.setMaximumWidth(40)
        btn_up.clicked.connect(self._on_move_scene_up)
        buttons_layout.addWidget(btn_up)
        
        btn_down = QPushButton("⬇️", self)
        btn_down.setToolTip("Переместить сцену вниз (позже в порядке генерации)")
        btn_down.setMaximumWidth(40)
        btn_down.clicked.connect(self._on_move_scene_down)
        buttons_layout.addWidget(btn_down)
        
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
        # Блокируем сигналы при программном обновлении выделения
        self._is_updating_selection = True
        try:
            self._refresh_scenes_list()
        finally:
            self._is_updating_selection = False
    
    def _refresh_scenes_list(self) -> None:
        """Обновить список сцен"""
        # Блокируем сигналы при обновлении списка
        self.scenes_list.blockSignals(True)
        try:
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
            
            # Принудительно обновляем виджет
            self.scenes_list.update()
        finally:
            self.scenes_list.blockSignals(False)
    
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
        
        # Устанавливаем новую сцену как текущую
        self._current_scene = new_scene
        
        # Сохраняем проект после добавления сцены
        # Получаем контроллер через родительское окно
        parent_window = self.window()
        if hasattr(parent_window, '_controller'):
            try:
                parent_window._controller.save_current_project()
            except Exception:
                pass  # Игнорируем ошибки сохранения
        
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
            
            # Сохраняем ID удаляемой сцены
            deleted_scene_id = scene_id
            
            # Удаляем сцену из проекта
            self._project.remove_scene(scene_id)
            
            # Проверяем, что сцена действительно удалена
            if self._project.find_scene(scene_id):
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось удалить сцену."
                )
                return
            
            # Если удаляемая сцена была текущей, сбрасываем текущую сцену
            if self._current_scene and self._current_scene.id == deleted_scene_id:
                self._current_scene = None
            
            # Обновляем список сцен
            # Сначала полностью очищаем список
            self.scenes_list.clear()
            
            # Затем заполняем заново
            if self._project:
                for scene in self._project.scenes:
                    item_text = f"{scene.name}\n  ({scene.label})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, scene.id)
                    self.scenes_list.addItem(item)
            
            # Принудительно обновляем виджет
            self.scenes_list.repaint()
            self.scenes_list.update()
            self.update()
            
            # Выбираем первую доступную сцену
            if self._project.scenes:
                new_scene = self._project.scenes[0]
                # Обновляем текущую сцену перед эмиссией сигнала
                self._current_scene = new_scene
                # Блокируем сигналы при программном обновлении
                self._is_updating_selection = True
                try:
                    # Выделяем новую сцену в списке
                    for i in range(self.scenes_list.count()):
                        item = self.scenes_list.item(i)
                        if item and item.data(Qt.UserRole) == new_scene.id:
                            self.scenes_list.setCurrentItem(item)
                            item.setSelected(True)
                            break
                finally:
                    self._is_updating_selection = False
                self.scene_selected.emit(new_scene)
            else:
                # Если сцен не осталось, сбрасываем текущую сцену
                self._current_scene = None
    
    def _on_scene_double_clicked(self, item: QListWidgetItem) -> None:
        """Обработка двойного клика по сцене"""
        scene_id = item.data(Qt.UserRole)
        if not self._project:
            return
        
        scene = self._project.find_scene(scene_id)
        if scene:
            # Проверяем, что это не та же сцена (избегаем лишних перезагрузок)
            if self._current_scene and self._current_scene.id == scene.id:
                return
            self.scene_selected.emit(scene)
    
    def _on_move_scene_up(self) -> None:
        """Переместить выбранную сцену вверх"""
        if not self._project:
            return
        
        current_item = self.scenes_list.currentItem()
        if not current_item:
            return
        
        scene_id = current_item.data(Qt.UserRole)
        if self._project.move_scene_up(scene_id):
            # Обновляем список сцен
            self._refresh_scenes_list()
            # Выделяем перемещенную сцену
            for i in range(self.scenes_list.count()):
                item = self.scenes_list.item(i)
                if item and item.data(Qt.UserRole) == scene_id:
                    self.scenes_list.setCurrentItem(item)
                    break
    
    def _on_move_scene_down(self) -> None:
        """Переместить выбранную сцену вниз"""
        if not self._project:
            return
        
        current_item = self.scenes_list.currentItem()
        if not current_item:
            return
        
        scene_id = current_item.data(Qt.UserRole)
        if self._project.move_scene_down(scene_id):
            # Обновляем список сцен
            self._refresh_scenes_list()
            # Выделяем перемещенную сцену
            for i in range(self.scenes_list.count()):
                item = self.scenes_list.item(i)
                if item and item.data(Qt.UserRole) == scene_id:
                    self.scenes_list.setCurrentItem(item)
                    break
    
    def _on_scene_selection_changed(self) -> None:
        """Обработка изменения выбора сцены"""
        # Игнорируем изменения во время программного обновления
        if self._is_updating_selection:
            return
        
        current_item = self.scenes_list.currentItem()
        if not current_item or not self._project:
            return
        
        scene_id = current_item.data(Qt.UserRole)
        scene = self._project.find_scene(scene_id)
        if scene:
            # Проверяем, что это не та же сцена (избегаем лишних перезагрузок)
            if self._current_scene and self._current_scene.id == scene.id:
                return
            self.scene_selected.emit(scene)
