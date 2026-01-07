from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtWidgets import QGraphicsPathItem


class ConnectionItem(QGraphicsPathItem):
    """
    Visualrepresentation of connection between ports:
    - drawn as cubic Bezier curve between two points
    - can be temporary (second end follows mouse) or permanent
    """

    def __init__(self, src_port, dst_port=None, parent=None):
        super().__init__(parent)

        self.src_port = src_port
        self.dst_port = dst_port

        self.setZValue(-1)
        self.setPen(QPen(QColor("#c0c0c0"), 2))

        self._tmp_end = None

        self.update_path()

    def set_tmp_end(self, pos: QPointF):
        """Temporary end for mouse during wire dragging"""
        self._tmp_end = pos
        self.update_path()

    def set_dst_port(self, port):
        """Final destination - input port"""
        self.dst_port = port
        self._tmp_end = None
        self.update_path()

    def update_path(self):
        """Redraw curve between ports"""
        if not self.src_port:
            return

        p1: QPointF = self.src_port.scenePos()

        if self.dst_port is not None:
            p2: QPointF = self.dst_port.scenePos()
        elif self._tmp_end is not None:
            p2: QPointF = self._tmp_end
        else:
            p2 = p1

        dx = (p2.x() - p1.x()) * 0.5
        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() - dx, p2.y())

        path = QPainterPath(p1)
        path.cubicTo(c1, c2, p2)
        self.setPath(path)

    def detach_from(self, port):
        """Detach wire from port (when deleting)"""
        if self.src_port == port:
            self.src_port = None
        if self.dst_port == port:
            self.dst_port = None
