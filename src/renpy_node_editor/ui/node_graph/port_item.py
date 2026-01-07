from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem


class PortItem(QGraphicsEllipseItem):
    """
    Порт ноды (вход/выход):
    - рисуется маленьким кружком
    - хранит список соединений (ConnectionItem)
    """

    def __init__(
        self,
        parent: Optional[QGraphicsItem] = None,
        is_output: bool = False,
        name: str = "",
    ) -> None:
        # кружок 8x8 с центром в (0,0)
        super().__init__(-4, -4, 8, 8, parent)

        self.is_output: bool = is_output
        self.name: str = name
        self.connections: List["ConnectionItem"] = []

        color = QColor("#ffcc66") if is_output else QColor("#66ccff")
        self.setBrush(QBrush(color))

        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    # ---- работа с соединениями ----

    def add_connection(self, conn: "ConnectionItem") -> None:
        if conn not in self.connections:
            self.connections.append(conn)

    def remove_connection(self, conn: "ConnectionItem") -> None:
        if conn in self.connections:
            self.connections.remove(conn)

    def clear_connections(self) -> None:
        for c in list(self.connections):
            # порт отвечает только за отцепление;
            # удаление самого QGraphicsItem должен делать владелец сцены
            c.detach_from(self)
        self.connections.clear()

    # ---- реакция на движение ----

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            for c in self.connections:
                c.update_path()
        return super().itemChange(change, value)

    # ---- немного визуального фан-сервиса ----

    def hoverEnterEvent(self, event) -> None:
        self.setBrush(QBrush(QColor("#ffffff")))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        color = QColor("#ffcc66") if self.is_output else QColor("#66ccff")
        self.setBrush(QBrush(color))
        super().hoverLeaveEvent(event)
