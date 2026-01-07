from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem

if TYPE_CHECKING:
    from renpy_node_editor.ui.node_graph.connection_item import ConnectionItem


class PortItem(QGraphicsEllipseItem):
    """
    Port of a node (input/output):
    - small circle (8x8)
    - stores list of connections
    - updates wires when moving
    """

    def __init__(
        self,
        parent: Optional[QGraphicsItem] = None,
        is_output: bool = False,
        name: str = "",
    ) -> None:
        super().__init__(-4, -4, 8, 8, parent)

        self.is_output: bool = is_output
        self.name: str = name
        self.connections: List[ConnectionItem] = []

        color = QColor("#ffcc66") if is_output else QColor("#66ccff")
        self.setBrush(QBrush(color))

        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    # ---- work with connections ----

    def add_connection(self, conn: ConnectionItem) -> None:
        if conn not in self.connections:
            self.connections.append(conn)

    def remove_connection(self, conn: ConnectionItem) -> None:
        if conn in self.connections:
            self.connections.remove(conn)

    def clear_connections(self) -> None:
        for c in list(self.connections):
            c.detach_from(self)
        self.connections.clear()

    # ---- reaction to movement ----

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            for c in self.connections:
                c.update_path()
        return super().itemChange(change, value)

    # ---- visual details ----

    def hoverEnterEvent(self, event) -> None:
        self.setBrush(QBrush(QColor("#ffffff")))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        color = QColor("#ffcc66") if self.is_output else QColor("#66ccff")
        self.setBrush(QBrush(color))
        super().hoverLeaveEvent(event)
