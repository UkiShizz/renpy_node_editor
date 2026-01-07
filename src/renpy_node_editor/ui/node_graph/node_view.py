from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent, QMouseEvent, QPainter, QKeyEvent
from PySide6.QtWidgets import QGraphicsView, QWidget

from renpy_node_editor.core.model import Project, Scene
from renpy_node_editor.ui.node_graph.node_scene import NodeScene


class NodeView(QGraphicsView):
    """
    Вьюха нодового графа:
    - держит NodeScene
    - зум колесом (с Ctrl)
    - панорамирование средней кнопкой
    - принимает drag&drop из палитры
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._scene = NodeScene(self)
        self.setScene(self._scene)

        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.NoDrag)
        # Используем FullViewportUpdate чтобы сетка всегда перерисовывалась
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setBackgroundBrush(self._scene.backgroundBrush())

        # важно: чтобы события dnd долетали до сцены
        self.setAcceptDrops(True)

        self._is_panning = False
        self._last_pan_pos: Optional[QPoint] = None

        # зум вокруг мыши
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    # ---- привязка к модели ----

    @property
    def node_scene(self) -> NodeScene:
        return self._scene

    def set_project_and_scene(self, project: Project, scene: Scene) -> None:
        """Установить проект и сцену - пересоздаем сцену для безопасности"""
        try:
            # Сохраняем текущее состояние view
            current_center = self.mapToScene(self.viewport().rect().center())
            
            # Создаем новую сцену вместо очистки старой
            old_scene = self._scene
            
            # Отключаем старую сцену от view
            self.setScene(None)
            
            # Создаем новую сцену
            self._scene = NodeScene(self)
            self.setScene(self._scene)
            
            # Восстанавливаем настройки view
            self.setRenderHint(QPainter.Antialiasing, True)
            self.setDragMode(QGraphicsView.NoDrag)
            self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
            self.setBackgroundBrush(self._scene.backgroundBrush())
            self.setAcceptDrops(True)
            
            # Удаляем старую сцену (будет удалена сборщиком мусора)
            if old_scene:
                try:
                    old_scene.deleteLater()
                except Exception:
                    pass
            
            # Устанавливаем проект и сцену в новую сцену
            self._scene.set_project_and_scene(project, scene)
            
            # Восстанавливаем центр view
            try:
                self.centerOn(current_center)
            except Exception:
                self.centerOn(0, 0)
        except Exception as e:
            import traceback
            print(f"Error in set_project_and_scene: {e}")
            print(traceback.format_exc())
            # Fallback - просто вызываем метод сцены
            try:
                self._scene.set_project_and_scene(project, scene)
            except Exception:
                pass
    
    def center_view(self) -> None:
        """Вернуться в центр рабочей области"""
        self.centerOn(0, 0)

    # ---- зум ----

    def wheelEvent(self, event: QWheelEvent) -> None:  # type: ignore[override]
        if event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            if angle == 0:
                return

            factor = 1.0015 ** angle
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    # ---- панорамирование ----

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._is_panning and self._last_pan_pos is not None:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MiddleButton and self._is_panning:
            self._is_panning = False
            self._last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)
    
    # ---- keyboard ----
    
    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Удаляем выбранные блоки
            self._scene.delete_selected_blocks()
            event.accept()
            return
        
        super().keyPressEvent(event)