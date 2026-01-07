from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QGraphicsPathItem
import math


class ConnectionItem(QGraphicsPathItem):
    """
    Professional connection visualization:
    - smooth bezier curves
    - gradient colors
    - better line style
    """

    def __init__(self, src_port, dst_port=None, parent=None, connection_id: str = None):
        super().__init__(parent)

        self.src_port = src_port
        self.dst_port = dst_port
        self.connection_id = connection_id  # ID связи в модели

        self.setZValue(-1)
        
        # Более яркая и толстая линия
        self._pen = QPen(QColor("#A0A0A0"), 3)
        self._pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(self._pen)

        self._tmp_end = None
        self._arrow_end = None
        self._arrow_direction = None

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
        """Redraw smooth curve between ports with arrow at the end"""
        if not self.src_port:
            return
        
        # Проверяем, что порт еще существует (не удален)
        try:
            p1: QPointF = self.src_port.scenePos()
        except RuntimeError:
            # Порт уже удален
            return

        if self.dst_port is not None:
            try:
                p2: QPointF = self.dst_port.scenePos()
            except RuntimeError:
                # Порт уже удален
                p2 = p1
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
        
        # Сохраняем конечную точку и направление для стрелки
        # Вычисляем касательный вектор к кривой Безье в конечной точке
        # Для кубической кривой Безье: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        # Производная в t=1: B'(1) = 3(P₃ - P₂), где P₃ = p2, P₂ = c2
        if self.dst_port is not None or self._tmp_end is not None:
            # Касательный вектор в конечной точке кубической кривой Безье
            # Направление от последней контрольной точки к конечной точке
            arrow_dx = p2.x() - c2.x()
            arrow_dy = p2.y() - c2.y()
            
            # Нормализуем вектор
            length = math.sqrt(arrow_dx * arrow_dx + arrow_dy * arrow_dy)
            if length > 0.001:  # Минимальная длина для избежания деления на ноль
                arrow_dx /= length
                arrow_dy /= length
            else:
                # Если кривая почти прямая, используем направление от начала к концу
                arrow_dx = p2.x() - p1.x()
                arrow_dy = p2.y() - p1.y()
                length = math.sqrt(arrow_dx * arrow_dx + arrow_dy * arrow_dy)
                if length > 0.001:
                    arrow_dx /= length
                    arrow_dy /= length
                else:
                    # Fallback: направление вправо (по умолчанию для правила правой руки)
                    arrow_dx = 1.0
                    arrow_dy = 0.0
            
            # Отступаем немного от конечной точки для лучшего визуального эффекта
            arrow_offset = 8  # Отступ от порта
            arrow_end_x = p2.x() - arrow_dx * arrow_offset
            arrow_end_y = p2.y() - arrow_dy * arrow_offset
            
            self._arrow_end = QPointF(arrow_end_x, arrow_end_y)
            self._arrow_direction = (arrow_dx, arrow_dy)
        else:
            self._arrow_end = None
            self._arrow_direction = None

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Кастомная отрисовка с эффектом свечения и стрелкой"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Рисуем тень
        shadow_pen = QPen(QColor(0, 0, 0, 40), 5)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(shadow_pen)
        painter.drawPath(self.path())
        
        # Основная линия
        super().paint(painter, option, widget)
        
        # Рисуем стрелку на конце соединения
        if self._arrow_end is not None and self._arrow_direction is not None:
            self._draw_arrow(painter, self._arrow_end, self._arrow_direction)
    
    def _draw_arrow(self, painter: QPainter, end_point: QPointF, direction: tuple[float, float]) -> None:
        """Нарисовать стрелку в конце соединения"""
        arrow_size = 10
        arrow_width = 6
        
        dx, dy = direction
        
        # Вычисляем перпендикулярный вектор для ширины стрелки
        perp_dx = -dy
        perp_dy = dx
        
        # Точка начала стрелки (немного отступаем от конечной точки)
        arrow_start = QPointF(
            end_point.x() - dx * arrow_size,
            end_point.y() - dy * arrow_size
        )
        
        # Вершины треугольника стрелки
        arrow_tip = end_point
        arrow_left = QPointF(
            arrow_start.x() + perp_dx * arrow_width / 2,
            arrow_start.y() + perp_dy * arrow_width / 2
        )
        arrow_right = QPointF(
            arrow_start.x() - perp_dx * arrow_width / 2,
            arrow_start.y() - perp_dy * arrow_width / 2
        )
        
        # Рисуем стрелку
        arrow_polygon = QPolygonF([arrow_tip, arrow_left, arrow_right])
        
        # Используем тот же цвет, что и у линии
        arrow_color = self._pen.color()
        painter.setBrush(arrow_color)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(arrow_polygon)

    def detach_from(self, port):
        """Detach wire from port (when deleting)"""
        if self.src_port == port:
            self.src_port = None
        if self.dst_port == port:
            self.dst_port = None
