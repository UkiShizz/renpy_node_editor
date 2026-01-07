from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsPathItem


class ConnectionItem(QGraphicsPathItem):
    """
    Professional connection visualization:
    - smooth bezier curves
    - gradient colors
    - better line style
    """

    def __init__(self, src_port, dst_port=None, parent=None):
        super().__init__(parent)

        self.src_port = src_port
        self.dst_port = dst_port

        self.setZValue(-1)
        
        # Более яркая и толстая линия
        self._pen = QPen(QColor("#A0A0A0"), 3)
        self._pen.setCapStyle(QPen.RoundCap)
        self._pen.setJoinStyle(QPen.RoundJoin)
        self.setPen(self._pen)

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
        
        # Меняем цвет на более яркий при установке связи
        self._pen.setColor(QColor("#C0C0C0"))
        self.setPen(self._pen)

    def update_path(self):
        """Redraw smooth curve between ports"""
        if not self.src_port:
            return

        p1: QPointF = self.src_port.scenePos()

        if self.dst_port is not None:
            p2: QPointF = self.dst_port.scenePos()
        elif self._tmp_end is not None:
            p2: QPointF = self._tmp_end
        else:
            p2 = p1

        # Более плавные кривые
        dx = abs(p2.x() - p1.x()) * 0.6
        if dx < 50:
            dx = 50
        
        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() - dx, p2.y())

        path = QPainterPath(p1)
        path.cubicTo(c1, c2, p2)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Кастомная отрисовка с эффектом свечения"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Рисуем тень
        shadow_pen = QPen(QColor(0, 0, 0, 40), 5)
        shadow_pen.setCapStyle(QPen.RoundCap)
        painter.setPen(shadow_pen)
        painter.drawPath(self.path())
        
        # Основная линия
        super().paint(painter, option, widget)

    def detach_from(self, port):
        """Detach wire from port (when deleting)"""
        if self.src_port == port:
            self.src_port = None
        if self.dst_port == port:
            self.dst_port = None
