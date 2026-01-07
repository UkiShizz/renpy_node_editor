from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem

if TYPE_CHECKING:
    from renpy_node_editor.ui.node_graph.connection_item import ConnectionItem


class PortItem(QGraphicsEllipseItem):
    """
    Professional port design with hover effects:
    - larger size
    - gradient fill
    - glow effect on hover
    """

    def __init__(
        self,
        parent: Optional[QGraphicsItem] = None,
        is_output: bool = False,
        name: str = "",
    ) -> None:
        # Увеличиваем размер порта
        super().__init__(-8, -8, 16, 16, parent)

        self.is_output: bool = is_output
        self.name: str = name
        self.connections: List[ConnectionItem] = []
        self._is_hovered = False

        # Цвета портов
        if is_output:
            self._base_color = QColor("#FFD700")  # Золотой для выходов
            self._hover_color = QColor("#FFED4E")
        else:
            self._base_color = QColor("#4A90E2")  # Синий для входов
            self._hover_color = QColor("#6BA3F0")

        self._update_appearance()

        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def _update_appearance(self) -> None:
        """Обновить внешний вид порта"""
        color = self._hover_color if self._is_hovered else self._base_color
        self.setBrush(QBrush(color))
        # Толстая обводка
        pen = QPen(QColor("#FFFFFF"), 2)
        self.setPen(pen)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Кастомная отрисовка с эффектом свечения при наведении"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        if self._is_hovered:
            # Эффект свечения
            glow_rect = QRectF(-12, -12, 24, 24)
            glow_brush = QBrush(self._hover_color.lighter(150))
            glow_brush.setColor(QColor(self._hover_color.red(), 
                                      self._hover_color.green(), 
                                      self._hover_color.blue(), 80))
            painter.setBrush(glow_brush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(glow_rect)
        
        # Основной круг
        super().paint(painter, option, widget)

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
        self._is_hovered = True
        self._update_appearance()
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._is_hovered = False
        self._update_appearance()
        self.update()
        super().hoverLeaveEvent(event)
