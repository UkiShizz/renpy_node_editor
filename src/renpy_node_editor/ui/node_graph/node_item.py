from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem

from renpy_node_editor.core.model import Block
from renpy_node_editor.ui.node_graph.port_item import PortItem


class NodeItem(QGraphicsRectItem):
    """
    Visual representation of block (Block):
    - rectangle with title
    - input/output ports on sides
    """

    WIDTH = 140
    HEIGHT = 60

    def __init__(self, block: Block, parent: Optional[QGraphicsItem] = None) -> None:
        super().__init__(parent)

        self.block = block

        # ВАЖНО: инициализируем inputs и outputs ДО setPos(), т.к. setPos() триггерит itemChange()
        self.inputs: List[PortItem] = []
        self.outputs: List[PortItem] = []

        self.setRect(QRectF(0, 0, self.WIDTH, self.HEIGHT))
        self.setBrush(QBrush(QColor("#333333")))
        self.setPen(QPen(QColor("#666666"), 1.5))

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

        # Только ПОСЛЕ инициализации атрибутов вызываем setPos
        self.setPos(block.x, block.y)

        self._title_item = QGraphicsTextItem(block.type.name, self)
        self._title_item.setDefaultTextColor(QColor("#ffffff"))
        self._title_item.setPos(6, 4)

        self._create_ports()

    def _create_ports(self) -> None:
        """Create input port on left and output port on right"""

        in_port = PortItem(parent=self, is_output=False, name="in")
        in_port.setPos(0, self.HEIGHT / 2)
        self.inputs.append(in_port)

        out_port = PortItem(parent=self, is_output=True, name="out")
        out_port.setPos(self.WIDTH, self.HEIGHT / 2)
        self.outputs.append(out_port)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            # обновляем все провода при движении ноды
            for p in self.inputs + self.outputs:
                for c in p.connections:
                    c.update_path()

            self.block.x = self.pos().x()
            self.block.y = self.pos().y()

        return super().itemChange(change, value)

    def setSelected(self, selected: bool) -> None:  # type: ignore[override]
        super().setSelected(selected)
        if selected:
            self.setPen(QPen(QColor("#ffaa00"), 2))
        else:
            self.setPen(QPen(QColor("#666666"), 1.5))
