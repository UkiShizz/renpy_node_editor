from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, Qt, QPointF, pyqtSignal
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneDragDropEvent, QGraphicsSceneMouseEvent

from renpy_node_editor.core.model import Project, Scene, Block, BlockType
from renpy_node_editor.ui.block_palette import MIME_NODE_TYPE
from renpy_node_editor.ui.node_graph.node_item import NodeItem
from renpy_node_editor.ui.node_graph.port_item import PortItem
from renpy_node_editor.ui.node_graph.connection_item import ConnectionItem


GRID_SMALL = 16
GRID_BIG = 64


class NodeScene(QGraphicsScene):
    """
    Scene of node editor:
    - draws grid
    - stores NodeItem's
    - accepts drag&drop from BlockPalette
    - supports creating connections with mouse
    """
    
    # Signal emitted when a node is selected/deselected
    node_selection_changed = pyqtSignal(object)  # emits Block or None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._project: Optional[Project] = None
        self._scene_model: Optional[Scene] = None

        self.setBackgroundBrush(QColor("#202020"))
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setSceneRect(-5000, -5000, 10000, 10000)

        self._drag_connection: Optional[ConnectionItem] = None
        self._drag_src_port: Optional[PortItem] = None
        
        # Connect selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)

    # ---- binding to model ----

    def set_project_and_scene(self, project: Project, scene: Scene) -> None:
        self.clear()
        self._project = project
        self._scene_model = scene

        for block in scene.blocks:
            self._create_node_item_for_block(block)

    def _create_node_item_for_block(self, block: Block) -> NodeItem:
        item = NodeItem(block)
        self.addItem(item)
        return item

    # ---- grid ----

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # type: ignore[override]
        super().drawBackground(painter, rect)

        left = int(rect.left()) - (int(rect.left()) % GRID_SMALL)
        top = int(rect.top()) - (int(rect.top()) % GRID_SMALL)

        painter.setPen(QPen(QColor("#303030"), 1))
        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += GRID_SMALL

        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += GRID_SMALL

        painter.setPen(QPen(QColor("#404040"), 1))
        left_big = int(rect.left()) - (int(rect.left()) % GRID_BIG)
        top_big = int(rect.top()) - (int(rect.top()) % GRID_BIG)

        x = left_big
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += GRID_BIG

        y = top_big
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += GRID_BIG

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