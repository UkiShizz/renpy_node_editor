from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QFont, QColor
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
    QLabel,
    QAbstractItemView,
)

from renpy_node_editor.core.model import BlockType


MIME_NODE_TYPE = "application/x-renpy-node-type"


class BlockPalette(QListWidget):
    """
    Professional block palette with modern design.
    Drag & drop elements to the node editor.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setViewMode(QListWidget.ListMode)
        self.setSpacing(4)
        self.setAlternatingRowColors(True)
        
        # Стиль палитры
        self.setStyleSheet("""
            QListWidget {
                background-color: #252525;
                border: 2px solid #3A3A3A;
                border-radius: 8px;
                color: #E0E0E0;
                font-size: 11px;
                padding: 4px;
            }
            QListWidget::item {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3A3A3A;
                border-color: #4A90E2;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                border-color: #6BA3F0;
                color: #FFFFFF;
            }
        """)

        self._populate_items()

    def _populate_items(self) -> None:
        """Заполнить палитру типами блоков с группировкой"""
        # Группируем блоки по категориям
        categories = {
            "Диалоги": [BlockType.SAY, BlockType.NARRATION],
            "Визуальные": [BlockType.SCENE, BlockType.SHOW, BlockType.HIDE],
            "Логика": [BlockType.IF, BlockType.MENU, BlockType.JUMP, BlockType.CALL, BlockType.LABEL],
            "Эффекты": [BlockType.PAUSE, BlockType.TRANSITION, BlockType.SOUND, BlockType.MUSIC],
            "Данные": [BlockType.SET_VAR, BlockType.RETURN],
        }
        
        for category, block_types in categories.items():
            # Заголовок категории
            header = QListWidgetItem(f"━━━ {category} ━━━")
            header.setFlags(Qt.NoItemFlags)  # Не выбирается
            header.setForeground(QColor("#888888"))
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            header.setFont(font)
            self.addItem(header)
            
            # Блоки категории
            for block_type in block_types:
                item = QListWidgetItem(f"  • {block_type.name}")
                item.setData(Qt.UserRole, block_type.name)
                self.addItem(item)

    # ---- drag&drop ----

    def startDrag(self, supportedActions: Qt.DropActions) -> None:  # type: ignore[override]
        item = self.currentItem()
        if item is None:
            return

        block_type_name = item.data(Qt.UserRole)
        if not block_type_name:
            return

        mime_data = QMimeData()
        mime_data.setData(MIME_NODE_TYPE, str(block_type_name).encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)


class BlockPalettePanel(QWidget):
    """
    Обёртка с заголовком для палитры блоков.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        title = QLabel("Блоки", self)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.palette = BlockPalette(self)
        layout.addWidget(self.palette)
