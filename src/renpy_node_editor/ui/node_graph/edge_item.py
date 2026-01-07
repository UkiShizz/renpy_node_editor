from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtWidgets import QGraphicsPathItem


class EdgeItem(QGraphicsPathItem):
    """
    Визуальная "проводка" между двумя точками (портами).
    Без интерактива: просто линия/кривая, которую двигаем через update_path().
    """

    def __init__(
        self,
        source_pos: QPointF,
        dest_pos: QPointF,
        parent: Optional[QGraphicsPathItem] = None,
    ) -> None:
        super().__init__(parent)

        self._source_pos = source_pos
        self._dest_pos = dest_pos

        pen = QPen(QColor("#AAAAAA"))
        pen.setWidthF(2.0)
        self.setPen(pen)

        self.setZValue(-1)  # ноды сверху, провода снизу

        self.update_path()

    # ---- координаты ----

    def set_source_pos(self, pos: QPointF) -> None:
        self._source_pos = pos
        self.update_path()

    def set_dest_pos(self, pos: QPointF) -> None:
        self._dest_pos = pos
        self.update_path()

    def source_pos(self) -> QPointF:
        return self._source_pos

    def dest_pos(self) -> QPointF:
        return self._dest_pos

    # ---- построение пути ----

    def update_path(self) -> None:
        """
        Пересчитать кривую между source и dest.
        Сейчас — простая bezier-кривая (как в большинстве нод-редакторов).
        """
        path = QPainterPath(self._source_pos)

        dx = (self._dest_pos.x() - self._source_pos.x()) * 0.5
        c1 = QPointF(self._source_pos.x() + dx, self._source_pos.y())
        c2 = QPointF(self._dest_pos.x() - dx, self._dest_pos.y())

        path.cubicTo(c1, c2, self._dest_pos)
        self.setPath(path)

    # Опционально можно переопределить boundingRect/shape,
    # но для простого случая QGraphicsPathItem делает это сам.
