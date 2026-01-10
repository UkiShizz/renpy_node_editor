from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter, QPolygonF, QLinearGradient, QBrush, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
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

        # Устанавливаем zValue выше блоков, чтобы соединения можно было кликать
        # Но ниже портов, чтобы порты были доступны для создания соединений
        self.setZValue(0)
        
        # Делаем соединение выделяемым
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # Отключаем перемещение для соединений
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        
        # Улучшенная линия с градиентом
        self._pen = QPen(QColor("#6A6A6A"), 2.5)
        self._pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(self._pen)
        
        # Цвета для градиента
        self._base_color = QColor("#6A6A6A")
        self._highlight_color = QColor("#4A9EFF")
        self._is_highlighted = False  # Флаг для подсветки при выделении

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
        self._pen.setColor(self._highlight_color)
        self._pen.setWidth(3)
        self.setPen(self._pen)
    
    def set_highlighted(self, highlighted: bool) -> None:
        """Установить подсветку соединения"""
        if self._is_highlighted != highlighted:
            self._is_highlighted = highlighted
            self.update()  # Принудительно обновляем отрисовку
    
    def setSelected(self, selected: bool) -> None:  # type: ignore[override]
        """Обработка выделения соединения"""
        super().setSelected(selected)
        self._is_highlighted = selected
        self.update()  # Принудительно обновляем отрисовку
    
    def shape(self) -> QPainterPath:
        """Увеличиваем область клика для соединения"""
        path = self.path()  # Используем путь соединения
        if path.isEmpty():
            return super().shape()
        
        # Создаем более широкую область для клика (stroke width ~15px для удобства)
        stroker = QPainterPathStroker()
        stroker.setWidth(15)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(path)
    
    def boundingRect(self) -> QRectF:
        """Увеличиваем bounding rect для лучшей обработки кликов"""
        rect = super().boundingRect()
        # Добавляем отступ для области клика
        return rect.adjusted(-5, -5, 5, 5)

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
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        path = self.path()
        if path.isEmpty():
            return
        
        # Рисуем тень для глубины
        shadow_opacity = 80 if self._is_highlighted else 50
        shadow_width = 5 if self._is_highlighted else 4
        shadow_pen = QPen(QColor(0, 0, 0, shadow_opacity), shadow_width)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        shadow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(shadow_pen)
        painter.drawPath(path)
        
        # Подсветка при выделении связанных блоков
        if self._is_highlighted:
            # Внешнее свечение
            glow_color = QColor(74, 158, 255, 100)  # #4A9EFF
            glow_pen = QPen(glow_color, 6)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(glow_pen)
            painter.drawPath(path)
        
        # Основная линия с градиентом
        if self.dst_port is not None:
            # Установленное соединение - используем градиент
            if self._is_highlighted:
                # Более яркий градиент для подсвеченного соединения
                gradient = QLinearGradient(path.pointAtPercent(0), path.pointAtPercent(1))
                highlight_blue = QColor(74, 158, 255)  # #4A9EFF
                gradient.setColorAt(0, highlight_blue.lighter(120))
                gradient.setColorAt(0.5, highlight_blue)
                gradient.setColorAt(1, highlight_blue.lighter(110))
                line_width = 4
            else:
                gradient = QLinearGradient(path.pointAtPercent(0), path.pointAtPercent(1))
                gradient.setColorAt(0, self._base_color.lighter(130))
                gradient.setColorAt(0.5, self._highlight_color)
                gradient.setColorAt(1, self._highlight_color.lighter(110))
                line_width = 3
            
            pen = QPen(QBrush(gradient), line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
        else:
            # Временное соединение - обычная линия
            temp_pen = QPen(self._base_color, 2.5)
            temp_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            temp_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(temp_pen)
        
        # Рисуем путь
        painter.drawPath(path)
        
        # Рисуем стрелку на конце соединения
        if self._arrow_end is not None and self._arrow_direction is not None:
            self._draw_arrow(painter, self._arrow_end, self._arrow_direction)
    
    def _draw_arrow(self, painter: QPainter, end_point: QPointF, direction: tuple[float, float]) -> None:
        """Нарисовать стрелку в конце соединения с улучшенным дизайном"""
        arrow_size = 12 if not self._is_highlighted else 14
        arrow_width = 7 if not self._is_highlighted else 8
        
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
        
        # Определяем цвет стрелки
        if self._is_highlighted:
            arrow_color = QColor(74, 158, 255)  # #4A9EFF
        elif self.dst_port is not None:
            arrow_color = self._highlight_color
        else:
            arrow_color = self._pen.color()
        
        # Рисуем свечение вокруг стрелки
        if self.dst_port is not None:
            glow_opacity = 120 if self._is_highlighted else 80
            glow_pen = QPen(QColor(arrow_color.red(), arrow_color.green(), arrow_color.blue(), glow_opacity), 6 if self._is_highlighted else 5)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(arrow_polygon)
        
        # Основная стрелка
        painter.setBrush(QBrush(arrow_color))
        painter.setPen(QPen(arrow_color.darker(120), 1.5 if self._is_highlighted else 1))
        painter.drawPolygon(arrow_polygon)

    def detach_from(self, port):
        """Detach wire from port (when deleting)"""
        if self.src_port == port:
            self.src_port = None
        if self.dst_port == port:
            self.dst_port = None
