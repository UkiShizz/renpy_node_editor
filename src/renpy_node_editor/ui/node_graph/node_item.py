from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem

from renpy_node_editor.core.model import Block


class NodeItem(QGraphicsItem):
    """
    Визуальная нода (блок) в редакторе.
    Пока: прямоугольник с заголовком, который можно таскать.
    Порты и провода прикрутим отдельными PortItem/EdgeItem.
    """

    WIDTH = 160.0
    HEIGHT = 80.0
    TITLE_HEIGHT = 20.0
    RADIUS = 4.0

    def __init__(self, block: Block, parent: Optional[QGraphicsItem] = None) -> None:
        super().__init__(parent)

        self.block = block  # ссылка на модель

        # позиции берём из модели
        self.setPos(QPointF(block.x, block.y))

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

    # ---- геометрия ----

    def boundingRect(self) -> QRectF:  # type: ignore[override]
        margin = 1.0
        return QRectF(
            -margin,
            -margin,
            self.WIDTH + margin * 2,
            self.HEIGHT + margin * 2,
        )

    # ---- отрисовка ----

    def paint(  # type: ignore[override]
        self,
        painter: QPainter,
        option,
        widget=None,
    ) -> None:
        rect = QRectF(0, 0, self.WIDTH, self.HEIGHT)
        title_rect = QRectF(0, 0, self.WIDTH, self.TITLE_HEIGHT)

        # фон
        body_color = QColor("#303030")
        title_color = QColor("#505050")
        border_color = QColor("#AAAAAA")
        if self.isSelected():
            border_color = QColor("#FFD700")

        painter.setRenderHint(QPainter.Antialiasing, True)

        # тело
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(body_color))
        painter.drawRoundedRect(rect, self.RADIUS, self.RADIUS)

        # заголовок
        painter.setBrush(QBrush(title_color))
        painter.drawRoundedRect(
            QRectF(rect.x(), rect.y(), rect.width(), self.TITLE_HEIGHT),
            self.RADIUS,
            self.RADIUS,
        )

        # граница
        pen = QPen(border_color)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, self.RADIUS, self.RADIUS)

        # текст заголовка: тип блока
        painter.setPen(QColor("#FFFFFF"))
        title = self.block.type.name
        painter.drawText(
            title_rect.adjusted(4, 0, -4, 0),
            Qt.AlignVCenter | Qt.AlignLeft,
            title,
        )

    # ---- синхронизация с моделью ----

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):  # type: ignore[override]
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = self.pos()
            # обновляем позицию блока в модели
            self.block.x = pos.x()
            self.block.y = pos.y()
            # тут же позже будем уведомлять сцену, чтобы она обновляла EdgeItem'ы
        return super().itemChange(change, value)
