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
from renpy_node_editor.core.i18n import tr
from renpy_node_editor.ui.tooltips import get_block_tooltip
from renpy_node_editor.ui.styles import get_list_widget_style


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
        self.setStyleSheet(get_list_widget_style() + """
            QListWidget {
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                border-color: #4A9EFF;
            }
        """)

        self._populate_items()

    def _populate_items(self) -> None:
        """Заполнить палитру типами блоков с группировкой"""
        # Группируем блоки по категориям согласно документации Ren'Py
        categories = {
            tr("ui.block_palette.category.dialogs", "📝 Диалоги и текст"): [
                BlockType.SAY, BlockType.NARRATION, BlockType.VOICE, 
                BlockType.CENTER, BlockType.TEXT
            ],
            tr("ui.block_palette.category.visual", "🖼️ Визуальные элементы"): [
                BlockType.SCENE, BlockType.SHOW, BlockType.HIDE, BlockType.IMAGE
            ],
            tr("ui.block_palette.category.logic", "🔀 Логика и управление"): [
                BlockType.START, BlockType.IF, BlockType.WHILE, BlockType.FOR, BlockType.MENU, 
                BlockType.JUMP, BlockType.CALL, BlockType.LABEL, BlockType.RETURN
            ],
            tr("ui.block_palette.category.effects", "🎬 Эффекты и переходы"): [
                BlockType.PAUSE, BlockType.TRANSITION, BlockType.WITH
            ],
            tr("ui.block_palette.category.audio", "🔊 Аудио"): [
                BlockType.SOUND, BlockType.MUSIC, BlockType.STOP_SOUND, 
                BlockType.STOP_MUSIC, BlockType.QUEUE_SOUND, BlockType.QUEUE_MUSIC
            ],
            tr("ui.block_palette.category.variables", "💾 Переменные и данные"): [
                BlockType.SET_VAR, BlockType.DEFAULT, BlockType.DEFINE, BlockType.PYTHON
            ],
            tr("ui.block_palette.category.definitions", "👤 Определения"): [
                BlockType.CHARACTER, BlockType.STYLE
            ],
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
                # Добавляем подсказку
                tooltip = get_block_tooltip(block_type)
                item.setToolTip(tooltip)
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

        title = QLabel(tr("ui.block_palette.title", "Блоки"), self)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.palette = BlockPalette(self)
        layout.addWidget(self.palette)
