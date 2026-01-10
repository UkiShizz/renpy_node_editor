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
        BlockType.VOICE: (QColor("#5B9BD5"), QColor("#7DB3E8"), QColor("#3A6B9A")),
        BlockType.CENTER: (QColor("#5B9BD5"), QColor("#7DB3E8"), QColor("#3A6B9A")),
        BlockType.TEXT: (QColor("#5B9BD5"), QColor("#7DB3E8"), QColor("#3A6B9A")),
        
        # Визуальные элементы - зеленый градиент
        BlockType.SCENE: (QColor("#70AD47"), QColor("#8FC966"), QColor("#4F7A2F")),
        BlockType.SHOW: (QColor("#92D050"), QColor("#A8E066"), QColor("#6B9A38")),
        BlockType.HIDE: (QColor("#A9D18E"), QColor("#C0E8A8"), QColor("#7A9A6A")),
        BlockType.IMAGE: (QColor("#70AD47"), QColor("#8FC966"), QColor("#4F7A2F")),
        
        # Логика - оранжевый/красный градиент
        BlockType.START: (QColor("#FFD700"), QColor("#FFE44D"), QColor("#CCAA00")),  # Золотой для стартового блока
        BlockType.IF: (QColor("#FF6B6B"), QColor("#FF8E8E"), QColor("#CC4545")),
        BlockType.ELIF: (QColor("#FF6B6B"), QColor("#FF8E8E"), QColor("#CC4545")),
        BlockType.ELSE: (QColor("#FF6B6B"), QColor("#FF8E8E"), QColor("#CC4545")),
        BlockType.WHILE: (QColor("#FF6B6B"), QColor("#FF8E8E"), QColor("#CC4545")),
        BlockType.FOR: (QColor("#FF6B6B"), QColor("#FF8E8E"), QColor("#CC4545")),
        BlockType.MENU: (QColor("#FFA07A"), QColor("#FFB896"), QColor("#CC7A5F")),
        BlockType.JUMP: (QColor("#FF8C00"), QColor("#FFA533"), QColor("#CC6F00")),
        BlockType.CALL: (QColor("#FF6347"), QColor("#FF8266"), QColor("#CC4E38")),
        BlockType.LABEL: (QColor("#FF7F50"), QColor("#FF9A70"), QColor("#CC653F")),
        
        # Эффекты - фиолетовый градиент
        BlockType.PAUSE: (QColor("#9B59B6"), QColor("#B573D1"), QColor("#6B3F7A")),
        BlockType.TRANSITION: (QColor("#8E44AD"), QColor("#A866C7"), QColor("#5E2D73")),
        BlockType.WITH: (QColor("#8E44AD"), QColor("#A866C7"), QColor("#5E2D73")),
        BlockType.SOUND: (QColor("#7D3C98"), QColor("#9A5CB3"), QColor("#5A2A6B")),
        BlockType.MUSIC: (QColor("#6C3483"), QColor("#8A4FA3"), QColor("#4A2356")),
        BlockType.STOP_MUSIC: (QColor("#6C3483"), QColor("#8A4FA3"), QColor("#4A2356")),
        BlockType.STOP_SOUND: (QColor("#7D3C98"), QColor("#9A5CB3"), QColor("#5A2A6B")),
        BlockType.QUEUE_MUSIC: (QColor("#6C3483"), QColor("#8A4FA3"), QColor("#4A2356")),
        BlockType.QUEUE_SOUND: (QColor("#7D3C98"), QColor("#9A5CB3"), QColor("#5A2A6B")),
        
        # Переменные - желтый градиент
        BlockType.SET_VAR: (QColor("#F39C12"), QColor("#F5B041"), QColor("#C27D0E")),
        BlockType.DEFAULT: (QColor("#F39C12"), QColor("#F5B041"), QColor("#C27D0E")),
        BlockType.DEFINE: (QColor("#F39C12"), QColor("#F5B041"), QColor("#C27D0E")),
        BlockType.PYTHON: (QColor("#F39C12"), QColor("#F5B041"), QColor("#C27D0E")),
        
        # Персонажи и определения - бирюзовый градиент
        BlockType.CHARACTER: (QColor("#1ABC9C"), QColor("#48C9B0"), QColor("#16A085")),
        BlockType.STYLE: (QColor("#1ABC9C"), QColor("#48C9B0"), QColor("#16A085")),
        
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
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        rect = self.rect()
        
        # Улучшенная тень с размытием
        shadow_offset = 8 if self._is_selected else 3
        shadow_opacity = 100 if self._is_selected else 40
        
        # Множественные тени для эффекта глубины
        for i in range(3):
            shadow_rect = rect.adjusted(
                shadow_offset + i, 
                shadow_offset + i, 
                shadow_offset + i, 
                shadow_offset + i
            )
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
            shadow_alpha = shadow_opacity - (i * 20)
            if shadow_alpha > 0:
                painter.fillPath(shadow_path, QColor(0, 0, 0, shadow_alpha))
        
        # Основной блок
        main_path = QPainterPath()
        main_path.addRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        
        # Подсветка фона при выделении
        if self._is_selected:
            # Внешнее свечение
            glow_path = QPainterPath()
            glow_rect = rect.adjusted(-4, -4, 4, 4)
            glow_path.addRoundedRect(glow_rect, self.CORNER_RADIUS + 4, self.CORNER_RADIUS + 4)
            glow_gradient = QLinearGradient(glow_rect.topLeft(), glow_rect.bottomLeft())
            highlight_color = QColor(74, 158, 255, 60)  # #4A9EFF с прозрачностью
            glow_gradient.setColorAt(0, highlight_color)
            glow_gradient.setColorAt(0.5, QColor(74, 158, 255, 40))
            glow_gradient.setColorAt(1, highlight_color)
            painter.fillPath(glow_path, QBrush(glow_gradient))
        
        # Улучшенный градиент для фона с большей глубиной
        if self._is_selected:
            # Более яркий градиент для выделенного блока
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            gradient.setColorAt(0, self._light_color.lighter(115))
            gradient.setColorAt(0.5, self._main_color.lighter(105))
            gradient.setColorAt(1, self._dark_color.darker(105))
        else:
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            gradient.setColorAt(0, self._light_color.lighter(105))
            gradient.setColorAt(0.5, self._main_color)
            gradient.setColorAt(1, self._dark_color.darker(110))
        painter.fillPath(main_path, QBrush(gradient))
        
        # Заголовок с другим градиентом
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), self.HEADER_HEIGHT)
        header_path = QPainterPath()
        header_path.addRoundedRect(header_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
        header_path.addRect(header_rect.x(), header_rect.y() + self.CORNER_RADIUS, 
                           header_rect.width(), header_rect.height() - self.CORNER_RADIUS)
        
        # Более яркий градиент для заголовка
        if self._is_selected:
            header_gradient = QLinearGradient(header_rect.topLeft(), header_rect.bottomLeft())
            header_gradient.setColorAt(0, self._main_color.lighter(130))
            header_gradient.setColorAt(0.5, self._main_color.lighter(120))
            header_gradient.setColorAt(1, self._main_color.lighter(110))
        else:
            header_gradient = QLinearGradient(header_rect.topLeft(), header_rect.bottomLeft())
            header_gradient.setColorAt(0, self._main_color.lighter(120))
            header_gradient.setColorAt(0.5, self._main_color.lighter(110))
            header_gradient.setColorAt(1, self._main_color)
        painter.fillPath(header_path, QBrush(header_gradient))
        
        # Обводка с эффектом свечения при выделении
        pen_width = 4 if self._is_selected else 2
        if self._is_selected:
            # Внешняя обводка (свечение)
            glow_color = QColor(74, 158, 255, 150)  # #4A9EFF
            glow_pen = QPen(glow_color, pen_width + 3)
            painter.setPen(glow_pen)
            painter.drawPath(main_path)
            # Средняя обводка
            mid_pen = QPen(QColor(255, 255, 255, 180), pen_width + 1)
            painter.setPen(mid_pen)
            painter.drawPath(main_path)
            # Основная обводка
            border_color = QColor("#FFFFFF")
        else:
            border_color = self._main_color.darker(120)
        
        painter.setPen(QPen(border_color, pen_width))
        painter.drawPath(main_path)
        
        # Разделительная линия под заголовком с градиентом
        line_y = self.HEADER_HEIGHT
        line_gradient = QLinearGradient(rect.x() + 8, line_y, rect.width() - 8, line_y)
        line_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        line_gradient.setColorAt(0.5, self._main_color.darker(150))
        line_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(line_gradient), 1.5))
        painter.drawLine(rect.x() + 8, line_y, rect.width() - 8, line_y)

    def _create_ports(self) -> None:
        """Create input port on left and output port(s) on right"""
        # START блок не имеет входного порта - это точка входа
        if self.block.type != BlockType.START:
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
        elif self.block.type == BlockType.WHILE or self.block.type == BlockType.FOR:
            # Циклы имеют один выход для тела цикла
            out_port = PortItem(parent=self, is_output=True, name="loop")
            out_port.setPos(self.WIDTH + 6, self.HEIGHT / 2)
            self.outputs.append(out_port)
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
            try:
                # Проверяем, что элемент еще в сцене
                scene = self.scene()
                if not scene:
                    return super().itemChange(change, value)
                
                # Проверяем, что сцена не загружается (предотвращаем обновления во время смены сцены)
                if hasattr(scene, '_is_loading') and scene._is_loading:
                    return super().itemChange(change, value)
                
                for p in self.inputs + self.outputs:
                    # Создаем копию списка connections для безопасной итерации
                    for c in list(p.connections):
                        try:
                            # Проверяем, что соединение еще в сцене
                            if c and c.scene():
                                c.update_path()
                        except (RuntimeError, AttributeError):
                            # Соединение уже удалено, удаляем из списка
                            if c in p.connections:
                                p.connections.remove(c)

                self.block.x = self.pos().x()
                self.block.y = self.pos().y()
                
                # Эмитим сигнал об изменении проекта (изменение позиции блока)
                if hasattr(scene, 'project_modified'):
                    scene.project_modified.emit()
            except Exception:
                # Игнорируем ошибки при обновлении путей
                pass

        return super().itemChange(change, value)

    def setSelected(self, selected: bool) -> None:  # type: ignore[override]
        super().setSelected(selected)
        self._is_selected = selected
        self.update()  # Принудительно обновляем отрисовку
    
    def _update_content(self) -> None:
        """Update the displayed content based on block properties"""
        # Remove old content item if it exists
        if self._content_item is not None:
            try:
                scene = self.scene()
                if scene is not None:
                    # Проверяем, что сцена не загружается
                    if hasattr(scene, '_is_loading') and scene._is_loading:
                        return
                    try:
                        scene.removeItem(self._content_item)
                    except (RuntimeError, AttributeError):
                        pass
                else:
                    try:
                        self._content_item.setParentItem(None)
                    except (RuntimeError, AttributeError):
                        pass
            except (RuntimeError, AttributeError):
                pass
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
        elif self.block.type == BlockType.VOICE:
            voice = params.get("voice_file", "")
            return f"voice: {voice}" if voice else ""
        elif self.block.type == BlockType.CENTER:
            text = params.get("text", "")
            return f"centered: {text[:30]}" if text else ""
        elif self.block.type == BlockType.TEXT:
            text = params.get("text", "")
            return f"text: {text[:30]}" if text else ""
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
        elif self.block.type == BlockType.WHILE:
            condition = params.get("condition", "")
            return f"while {condition[:30]}" if condition else "while ..."
        elif self.block.type == BlockType.FOR:
            var = params.get("variable", "")
            iterable = params.get("iterable", "")
            if var and iterable:
                return f"for {var} in {iterable[:20]}"
            return f"for {var}..." if var else "for ..."
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
        elif self.block.type == BlockType.IMAGE:
            name = params.get("name", "")
            return f"image {name}" if name else ""
        elif self.block.type == BlockType.SET_VAR:
            var = params.get("variable", "")
            val = params.get("value", "")
            if var and val:
                return f"{var} = {val}"
            return var if var else ""
        elif self.block.type == BlockType.DEFAULT:
            var = params.get("variable", "")
            val = params.get("value", "")
            if var and val:
                return f"default {var} = {val}"
            return f"default {var}" if var else ""
        elif self.block.type == BlockType.DEFINE:
            name = params.get("name", "")
            val = params.get("value", "")
            if name and val:
                return f"define {name} = {val}"
            return f"define {name}" if name else ""
        elif self.block.type == BlockType.PYTHON:
            code = params.get("code", "")
            return f"python: {code[:30]}..." if code else "python: ..."
        elif self.block.type == BlockType.CHARACTER:
            name = params.get("name", "")
            return f"character {name}" if name else ""
        elif self.block.type == BlockType.PAUSE:
            duration = params.get("duration", "")
            return f"pause {duration}s" if duration else ""
        elif self.block.type == BlockType.TRANSITION:
            trans = params.get("transition", "")
            return f"with {trans}" if trans else ""
        elif self.block.type == BlockType.WITH:
            trans = params.get("transition", "")
            return f"with {trans}" if trans else ""
        elif self.block.type == BlockType.SOUND:
            sound = params.get("sound_file", "")
            return f"sound: {sound}" if sound else ""
        elif self.block.type == BlockType.MUSIC:
            music = params.get("music_file", "")
            return f"music: {music}" if music else ""
        elif self.block.type == BlockType.STOP_MUSIC:
            fadeout = params.get("fadeout", "")
            return f"stop music{f' fadeout {fadeout}' if fadeout else ''}"
        elif self.block.type == BlockType.STOP_SOUND:
            fadeout = params.get("fadeout", "")
            return f"stop sound{f' fadeout {fadeout}' if fadeout else ''}"
        elif self.block.type == BlockType.QUEUE_MUSIC:
            music = params.get("music_file", "")
            return f"queue music: {music}" if music else ""
        elif self.block.type == BlockType.QUEUE_SOUND:
            sound = params.get("sound_file", "")
            return f"queue sound: {sound}" if sound else ""
        elif self.block.type == BlockType.RETURN:
            return "return"
        elif self.block.type == BlockType.STYLE:
            name = params.get("name", "")
            return f"style {name}" if name else ""
        elif self.block.type == BlockType.ELIF:
            condition = params.get("condition", "")
            return f"elif {condition[:30]}" if condition else "elif ..."
        elif self.block.type == BlockType.ELSE:
            return "else"
        elif self.block.type == BlockType.EXTEND:
            text = params.get("text", "")
            return f"extend: {text[:30]}" if text else "extend"
        elif self.block.type == BlockType.INTERJECT:
            text = params.get("text", "")
            return f"interject: {text[:30]}" if text else "interject"
        
        return ""
    
    def update_display(self) -> None:
        """Public method to refresh the display after properties change"""
        self._update_content()
