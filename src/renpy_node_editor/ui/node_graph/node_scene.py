from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QKeyEvent
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsSceneDragDropEvent, QGraphicsSceneMouseEvent,
    QGraphicsSceneContextMenuEvent, QMenu, QMessageBox
)

from renpy_node_editor.core.model import Project, Scene, Block, BlockType, Connection, Port, PortDirection
from renpy_node_editor.ui.block_palette import MIME_NODE_TYPE
from renpy_node_editor.ui.node_graph.node_item import NodeItem
from renpy_node_editor.ui.node_graph.port_item import PortItem
from renpy_node_editor.ui.node_graph.connection_item import ConnectionItem


GRID_SMALL = 20
GRID_BIG = 100


class NodeScene(QGraphicsScene):
    """
    Professional node editor scene:
    - modern grid design
    - better background
    - smooth visuals
    """
    
    # Signal emitted when a node is selected/deselected
    node_selection_changed = Signal(object)  # emits Block or None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._project: Optional[Project] = None
        self._scene_model: Optional[Scene] = None

        # Современная темная тема с бесконечной областью
        self.setBackgroundBrush(QColor("#1E1E1E"))
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        # Бесконечная рабочая область (очень большой размер)
        self.setSceneRect(-100000, -100000, 200000, 200000)

        self._drag_connection: Optional[ConnectionItem] = None
        self._drag_src_port: Optional[PortItem] = None
        
        # Connect selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)

    # ---- binding to model ----

    def set_project_and_scene(self, project: Project, scene: Scene) -> None:
        self.clear()
        self._project = project
        self._scene_model = scene

        # Создаем блоки
        for block in scene.blocks:
            self._create_node_item_for_block(block)
        
        # Создаем связи
        self._create_connections()

    def _create_node_item_for_block(self, block: Block) -> NodeItem:
        item = NodeItem(block)
        self.addItem(item)
        return item
    
    def _create_connections(self) -> None:
        """Создать визуальные связи из модели"""
        if not self._scene_model:
            return
        
        # Создаем маппинг port_id -> PortItem
        port_items: dict[str, PortItem] = {}
        for item in self.items():
            if isinstance(item, NodeItem):
                for port in item.inputs + item.outputs:
                    # Нужно найти port_id для этого порта
                    # Для этого создадим порты в модели если их нет
                    port_id = self._get_or_create_port_id(item.block, port)
                    port_items[port_id] = port
        
        # Создаем связи
        for conn in self._scene_model.connections:
            src_port_item = port_items.get(conn.from_port_id)
            dst_port_item = port_items.get(conn.to_port_id)
            
            if src_port_item and dst_port_item:
                connection_item = ConnectionItem(
                    src_port=src_port_item,
                    dst_port=dst_port_item,
                    connection_id=conn.id
                )
                self.addItem(connection_item)
                src_port_item.add_connection(connection_item)
                dst_port_item.add_connection(connection_item)
    
    def _get_or_create_port_id(self, block: Block, port_item: PortItem) -> str:
        """Получить или создать port_id для порта"""
        if not self._scene_model:
            return str(id(port_item))
        
        # Ищем существующий порт
        for port in self._scene_model.ports:
            if port.node_id == block.id:
                # Проверяем по направлению и позиции
                is_output = port_item.is_output
                if (port.direction == PortDirection.OUTPUT and is_output) or \
                   (port.direction == PortDirection.INPUT and not is_output):
                    return port.id
        
        # Создаем новый порт
        port_id = str(id(port_item))
        port = Port(
            id=port_id,
            node_id=block.id,
            name=port_item.name,
            direction=PortDirection.OUTPUT if port_item.is_output else PortDirection.INPUT
        )
        self._scene_model.add_port(port)
        return port_id

    # ---- grid ----

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # type: ignore[override]
        """Отрисовка фона и сетки"""
        # Рисуем базовый фон
        painter.fillRect(rect, QBrush(QColor("#1E1E1E")))
        
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

        # Мелкая сетка - более контрастная
        self._draw_grid_lines(painter, rect, GRID_SMALL, QColor("#2D2D2D"), 1)
        
        # Крупная сетка - еще более заметная
        self._draw_grid_lines(painter, rect, GRID_BIG, QColor("#3D3D3D"), 2)
        
        # Центральные линии - самые заметные
        painter.setPen(QPen(QColor("#5A5A5A"), 3))
        if rect.left() <= 0 <= rect.right():
            painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))
        if rect.top() <= 0 <= rect.bottom():
            painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
    
    def _draw_grid_lines(self, painter: QPainter, rect: QRectF, step: int, color: QColor, width: int) -> None:
        """Вспомогательный метод для отрисовки линий сетки"""
        painter.setPen(QPen(color, width))
        
        # Вертикальные линии
        left = int(rect.left()) - (int(rect.left()) % step)
        x = left
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += step

        # Горизонтальные линии
        top = int(rect.top()) - (int(rect.top()) % step)
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += step

    # ---- drag&drop from palette ----

    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasFormat(MIME_NODE_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasFormat(MIME_NODE_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QGraphicsSceneDragDropEvent) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if not mime.hasFormat(MIME_NODE_TYPE):
            event.ignore()
            return

        if not self._scene_model:
            event.ignore()
            return

        data = mime.data(MIME_NODE_TYPE)
        if not data:
            event.ignore()
            return

        block_type_name = bytes(data).decode("utf-8")

        try:
            block_type = BlockType[block_type_name]
        except KeyError:
            event.ignore()
            return

        pos: QPointF = event.scenePos()

        block = Block(
            id=str(id(object())),
            type=block_type,
            params={},
            x=pos.x(),
            y=pos.y(),
        )
        self._scene_model.add_block(block)

        self._create_node_item_for_block(block)

        event.acceptProposedAction()

    # ---- connections with mouse ----

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # type: ignore[override]
        view = self.views()[0] if self.views() else None
        item = self.itemAt(event.scenePos(), view.transform()) if view else None

        if event.button() == Qt.LeftButton and isinstance(item, PortItem) and item.is_output:
            self._drag_src_port = item
            self._drag_connection = ConnectionItem(src_port=item)
            self.addItem(self._drag_connection)
            self._drag_connection.set_tmp_end(event.scenePos())
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # type: ignore[override]
        if self._drag_connection is not None:
            self._drag_connection.set_tmp_end(event.scenePos())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # type: ignore[override]
        if self._drag_connection is not None and self._drag_src_port is not None:
            view = self.views()[0] if self.views() else None
            item = self.itemAt(event.scenePos(), view.transform()) if view else None

            if isinstance(item, PortItem) and not item.is_output:
                # Создаем связь в модели
                if self._scene_model:
                    from_port_id = self._get_or_create_port_id(
                        self._drag_src_port.parentItem().block if isinstance(self._drag_src_port.parentItem(), NodeItem) else None,
                        self._drag_src_port
                    )
                    to_port_id = self._get_or_create_port_id(
                        item.parentItem().block if isinstance(item.parentItem(), NodeItem) else None,
                        item
                    )
                    
                    connection_id = str(id(self._drag_connection))
                    connection = Connection(
                        id=connection_id,
                        from_port_id=from_port_id,
                        to_port_id=to_port_id
                    )
                    self._scene_model.add_connection(connection)
                    self._drag_connection.connection_id = connection_id
                
                self._drag_connection.set_dst_port(item)
                self._drag_src_port.add_connection(self._drag_connection)
                item.add_connection(self._drag_connection)
            else:
                self.removeItem(self._drag_connection)
                del self._drag_connection

            self._drag_connection = None
            self._drag_src_port = None
            event.accept()
            return

        super().mouseReleaseEvent(event)
    
    # ---- selection handling ----
    
    def _on_selection_changed(self) -> None:
        """Handle selection changes and emit signal with selected block"""
        selected_items = self.selectedItems()
        if selected_items:
            # Get the first selected item
            item = selected_items[0]
            if isinstance(item, NodeItem):
                self.node_selection_changed.emit(item.block)
            else:
                self.node_selection_changed.emit(None)
        else:
            self.node_selection_changed.emit(None)
    
    # ---- deletion ----
    
    def delete_selected_blocks(self) -> None:
        """Удалить выбранные блоки"""
        selected_items = [item for item in self.selectedItems() if isinstance(item, NodeItem)]
        if not selected_items:
            return
        
        if not self._scene_model:
            return
        
        # Подтверждение удаления
        count = len(selected_items)
        if count == 1:
            block_name = selected_items[0].block.type.name
            message = f"Вы уверены, что хотите удалить блок '{block_name}'?"
        else:
            message = f"Вы уверены, что хотите удалить {count} блоков?"
        
        reply = QMessageBox.question(
            None,  # Используем None чтобы диалог был модальным
            "Удаление блоков",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                # Сначала очищаем все связи от портов
                for port in item.inputs + item.outputs:
                    # Создаем копию списка connections
                    connections_copy = list(port.connections)
                    for conn in connections_copy:
                        # Удаляем связь из модели
                        if conn.connection_id and self._scene_model:
                            self._scene_model.remove_connection(conn.connection_id)
                        # Отсоединяем от портов
                        if conn.src_port and conn in conn.src_port.connections:
                            conn.src_port.remove_connection(conn)
                        if conn.dst_port and conn in conn.dst_port.connections:
                            conn.dst_port.remove_connection(conn)
                        # Удаляем визуально
                        if conn in self.items():
                            self.removeItem(conn)
                
                # Удаляем из модели (это также удалит порты)
                self._scene_model.remove_block(item.block.id)
                # Удаляем визуально
                self.removeItem(item)
    
    def delete_connection(self, connection_item: ConnectionItem) -> None:
        """Удалить связь"""
        if not self._scene_model or not connection_item.connection_id:
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            None,
            "Удаление связи",
            "Вы уверены, что хотите удалить эту связь?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Удаляем из модели
            self._scene_model.remove_connection(connection_item.connection_id)
            
            # Отсоединяем от портов
            if connection_item.src_port:
                connection_item.src_port.remove_connection(connection_item)
            if connection_item.dst_port:
                connection_item.dst_port.remove_connection(connection_item)
            
            # Удаляем визуально
            self.removeItem(connection_item)
    
    # ---- context menu ----
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:  # type: ignore[override]
        """Обработка контекстного меню (ПКМ)"""
        view = self.views()[0] if self.views() else None
        item = self.itemAt(event.scenePos(), view.transform()) if view else None
        
        if isinstance(item, NodeItem):
            # Контекстное меню для блока
            menu = QMenu()
            delete_action = menu.addAction("🗑️ Удалить блок")
            delete_action.triggered.connect(lambda: self.delete_selected_blocks())
            menu.exec(event.screenPos())
        elif isinstance(item, ConnectionItem):
            # Контекстное меню для связи
            menu = QMenu()
            delete_action = menu.addAction("🗑️ Удалить связь")
            delete_action.triggered.connect(lambda: self.delete_connection(item))
            menu.exec(event.screenPos())