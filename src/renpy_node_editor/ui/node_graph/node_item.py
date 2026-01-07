from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QPainterPath, QFont, QLinearGradient
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem

from renpy_node_editor.core.model import Block, BlockType
from renpy_node_editor.ui.node_graph.port_item import PortItem


def _get_block_colors(block_type: BlockType) -> tuple[QColor, QColor, QColor]:
    """Возвращает цвета блока: основной, светлый, темный"""
    color_map = {
        # Диалоги и текст - синий градиент
        BlockType.SAY: (QColor("#4A90E2"), QColor("#6BA3F0"), QColor("#2E5C8A")),
        BlockType.NARRATION: (QColor("#5B9BD5"), QColor("#7DB3E8"), QColor("#3A6B9A")),
        
        # Визуальные элементы - зеленый градиент
        BlockType.SCENE: (QColor("#70AD47"), QColor("#8FC966"), QColor("#4F7A2F")),
        BlockType.SHOW: (QColor("#92D050"), QColor("#A8E066"), QColor("#6B9A38")),
        BlockType.HIDE: (QColor("#A9D18E"), QColor("#C0E8A8"), QColor("#7A9A6A")),
        
        # Логика - оранжевый/красный градиент
        BlockType.IF: (QColor("#FF6B6B"), QColor("#FF8E8E"), QColor("#CC4545")),
        BlockType.MENU: (QColor("#FFA07A"), QColor("#FFB896"), QColor("#CC7A5F")),
        BlockType.JUMP: (QColor("#FF8C00"), QColor("#FFA533"), QColor("#CC6F00")),
        BlockType.CALL: (QColor("#FF6347"), QColor("#FF8266"), QColor("#CC4E38")),
        BlockType.LABEL: (QColor("#FF7F50"), QColor("#FF9A70"), QColor("#CC653F")),
        
        # Эффекты - фиолетовый градиент
        BlockType.PAUSE: (QColor("#9B59B6"), QColor("#B573D1"), QColor("#6B3F7A")),
        BlockType.TRANSITION: (QColor("#8E44AD"), QColor("#A866C7"), QColor("#5E2D73")),
        BlockType.SOUND: (QColor("#7D3C98"), QColor("#9A5CB3"), QColor("#5A2A6B")),
        BlockType.MUSIC: (QColor("#6C3483"), QColor("#8A4FA3"), QColor("#4A2356")),
        
        # Переменные - желтый градиент
        BlockType.SET_VAR: (QColor("#F39C12"), QColor("#F5B041"), QColor("#C27D0E")),
        
        # Структура - серый градиент
        BlockType.RETURN: (QColor("#95A5A6"), QColor("#B0C4C5"), QColor("#6B7A7A")),
    }
    return color_map.get(block_type, (QColor("#34495E"), QColor("#5D6D7E"), QColor("#1B2631")))


class NodeItem(QGraphicsRectItem):
    """
    Professional visual representation of block with modern design:
    - rounded corners
    - gradient fills
    - shadows
    - better typography
    """

    WIDTH = 200
    HEIGHT = 90
    CORNER_RADIUS = 12
    HEADER_HEIGHT = 32

    def __init__(self, block: Block, parent: Optional[QGraphicsItem] = None) -> None:
        super().__init__(parent)

        self.block = block
        self._is_selected = False

        # ВАЖНО: инициализируем inputs и outputs ДО setPos()
        self.inputs: List[PortItem] = []
        self.outputs: List[PortItem] = []

        # Получаем цвета для блока
        self._main_color, self._light_color, self._dark_color = _get_block_colors(block.type)

        self.setRect(QRectF(0, 0, self.WIDTH, self.HEIGHT))
        
        # Прозрачный фон для кастомной отрисовки
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.transparent))

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

        # Устанавливаем позицию
        self.setPos(block.x, block.y)

        # Заголовок блока
        self._title_item = QGraphicsTextItem(block.type.name, self)
        title_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self._title_item.setFont(title_font)
        self._title_item.setDefaultTextColor(QColor("#FFFFFF"))
        self._title_item.setPos(12, 8)

        self._content_item: Optional[QGraphicsTextItem] = None

        self._create_ports()
        self._update_content()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Кастомная отрисовка блока с градиентами и тенями"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        rect = self.rect()
        
        # Тень
        if self._is_selected:
            shadow_rect = rect.adjusted(4, 4, 4, 4)
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
            painter.fillPath(shadow_path, QColor(0, 0, 0, 60))
        
        # Основной блок
        main_path = QPainterPath()
        main_path.addRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        
        # Градиент для фона
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0, self._light_color)
        gradient.setColorAt(1, self._dark_color)
        painter.fillPath(main_path, QBrush(gradient))
        
        # Заголовок с другим градиентом
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), self.HEADER_HEIGHT)
        header_path = QPainterPath()
        header_path.addRoundedRect(header_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        header_path.addRect(header_rect.x(), header_rect.y() + self.CORNER_RADIUS, 
                           header_rect.width(), header_rect.height() - self.CORNER_RADIUS)
        
        header_gradient = QLinearGradient(header_rect.topLeft(), header_rect.bottomLeft())
        header_gradient.setColorAt(0, self._main_color.lighter(110))
        header_gradient.setColorAt(1, self._main_color)
        painter.fillPath(header_path, QBrush(header_gradient))
        
        # Обводка
        pen_width = 3 if self._is_selected else 2
        border_color = QColor("#FFFFFF") if self._is_selected else self._main_color.darker(120)
        painter.setPen(QPen(border_color, pen_width))
        painter.drawPath(main_path)
        
        # Разделительная линия под заголовком
        line_y = self.HEADER_HEIGHT
        painter.setPen(QPen(self._main_color.darker(130), 1))
        painter.drawLine(rect.x() + 8, line_y, rect.width() - 8, line_y)

    def _create_ports(self) -> None:
        """Create input port on left and output port(s) on right"""
        # Входной порт слева
        in_port = PortItem(parent=self, is_output=False, name="in")
        in_port.setPos(-6, self.HEIGHT / 2)
        self.inputs.append(in_port)

        # Выходные порты справа
        if self.block.type == BlockType.IF:
            # IF блок имеет два выхода: True и False
            true_port = PortItem(parent=self, is_output=True, name="True")
            true_port.setPos(self.WIDTH + 6, self.HEIGHT / 3)
            self.outputs.append(true_port)
            
            false_port = PortItem(parent=self, is_output=True, name="False")
            false_port.setPos(self.WIDTH + 6, self.HEIGHT * 2 / 3)
            self.outputs.append(false_port)
        elif self.block.type == BlockType.MENU:
            # MENU может иметь несколько выходов
            out_port = PortItem(parent=self, is_output=True, name="out")
            out_port.setPos(self.WIDTH + 6, self.HEIGHT / 2)
            self.outputs.append(out_port)
        else:
            # Обычный блок - один выход
            out_port = PortItem(parent=self, is_output=True, name="out")
            out_port.setPos(self.WIDTH + 6, self.HEIGHT / 2)
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
        self._is_selected = selected
        self.update()  # Перерисовываем с новым состоянием
    
    def _update_content(self) -> None:
        """Update the displayed content based on block properties"""
        # Remove old content item if it exists
        if self._content_item is not None:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self._content_item)
            else:
                self._content_item.setParentItem(None)
            self._content_item = None
        
        # Get a preview text based on block type and params
        preview_text = self._get_preview_text()
        if preview_text:
            self._content_item = QGraphicsTextItem(preview_text, self)
            content_font = QFont("Segoe UI", 9)
            self._content_item.setFont(content_font)
            self._content_item.setDefaultTextColor(QColor("#E8E8E8"))
            self._content_item.setPos(12, self.HEADER_HEIGHT + 8)
            # Limit text width to fit in node
            text_width = self.WIDTH - 24
            self._content_item.setTextWidth(text_width)
            # Truncate if too long
            if self._content_item.boundingRect().height() > 50:
                plain_text = self._content_item.toPlainText()
                if len(plain_text) > 40:
                    self._content_item.setPlainText(plain_text[:37] + "...")
    
    def _get_preview_text(self) -> str:
        """Get a short preview text from block params"""
        params = self.block.params
        
        if self.block.type == BlockType.SAY:
            text = params.get("text", "")
            who = params.get("who", "")
            if who:
                return f"{who}: {text[:25]}" if text else who
            return text[:35] if text else ""
        elif self.block.type == BlockType.NARRATION:
            text = params.get("text", "")
            return text[:35] if text else ""
        elif self.block.type == BlockType.JUMP:
            target = params.get("target", "")
            return f"→ {target}" if target else ""
        elif self.block.type == BlockType.CALL:
            label = params.get("label", "")
            return f"call {label}" if label else ""
        elif self.block.type == BlockType.LABEL:
            label = params.get("label", "")
            return f"label: {label}" if label else ""
        elif self.block.type == BlockType.IF:
            condition = params.get("condition", "")
            return condition[:35] if condition else "if ..."
        elif self.block.type == BlockType.MENU:
            question = params.get("question", "")
            choices = params.get("choices", [])
            choice_count = len(choices) if isinstance(choices, list) else 0
            if question:
                return f"{question[:25]}... ({choice_count})" if len(question) > 25 else f"{question} ({choice_count})"
            return f"Menu ({choice_count} choices)"
        elif self.block.type == BlockType.SCENE:
            bg = params.get("background", "")
            return f"scene {bg}" if bg else ""
        elif self.block.type == BlockType.SHOW:
            char = params.get("character", "")
            return f"show {char}" if char else ""
        elif self.block.type == BlockType.HIDE:
            char = params.get("character", "")
            return f"hide {char}" if char else ""
        elif self.block.type == BlockType.SET_VAR:
            var = params.get("variable", "")
            val = params.get("value", "")
            if var and val:
                return f"{var} = {val}"
            return var if var else ""
        elif self.block.type == BlockType.PAUSE:
            duration = params.get("duration", "")
            return f"pause {duration}s" if duration else ""
        elif self.block.type == BlockType.TRANSITION:
            trans = params.get("transition", "")
            return f"with {trans}" if trans else ""
        elif self.block.type == BlockType.SOUND:
            sound = params.get("sound_file", "")
            return f"sound: {sound}" if sound else ""
        elif self.block.type == BlockType.MUSIC:
            music = params.get("music_file", "")
            return f"music: {music}" if music else ""
        
        return ""
    
    def update_display(self) -> None:
        """Public method to refresh the display after properties change"""
        self._update_content()
