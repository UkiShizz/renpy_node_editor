from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem

from renpy_node_editor.core.model import Block, BlockType
from renpy_node_editor.ui.node_graph.port_item import PortItem


class NodeItem(QGraphicsRectItem):
    """
    Visual representation of block (Block):
    - rectangle with title
    - input/output ports on sides
    - displays key properties
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

        self._content_item: Optional[QGraphicsTextItem] = None

        self._create_ports()
        self._update_content()

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
    
    def _update_content(self) -> None:
        """Update the displayed content based on block properties"""
        # Remove old content item if it exists
        if self._content_item is not None:
            self.scene().removeItem(self._content_item)
            self._content_item = None
        
        # Get a preview text based on block type and params
        preview_text = self._get_preview_text()
        if preview_text:
            self._content_item = QGraphicsTextItem(preview_text, self)
            self._content_item.setDefaultTextColor(QColor("#aaaaaa"))
            self._content_item.setPos(6, 24)
            # Limit text width to fit in node
            text_width = self.WIDTH - 12
            self._content_item.setTextWidth(text_width)
            # Truncate if too long
            if self._content_item.boundingRect().height() > 30:
                # Show only first line
                plain_text = self._content_item.toPlainText()
                if len(plain_text) > 30:
                    self._content_item.setPlainText(plain_text[:27] + "...")
    
    def _get_preview_text(self) -> str:
        """Get a short preview text from block params"""
        params = self.block.params
        
        if self.block.type == BlockType.SAY:
            text = params.get("text", "")
            who = params.get("who", "")
            if who:
                return f"{who}: {text[:20]}" if text else who
            return text[:30] if text else ""
        elif self.block.type == BlockType.NARRATION:
            text = params.get("text", "")
            return text[:30] if text else ""
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
            return condition[:30] if condition else ""
        elif self.block.type == BlockType.MENU:
            question = params.get("question", "")
            return question[:30] if question else ""
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