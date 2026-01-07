from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
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
    Список доступных типов блоков.
    Таскаем элементы в рабочую область (NodeView/NodeScene) через drag&drop.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setViewMode(QListWidget.ListMode)
        self.setSpacing(2)
        self.setAlternatingRowColors(True)

        self._populate_items()

    def _populate_items(self) -> None:
        """
        Забиваем палитру базовыми типами из BlockType.
        Потом можно будет грузить из configs/blocks_schema.json.
        """
        for block_type in BlockType:
            item = QListWidgetItem(block_type.name)
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
        # просто кладём имя типа как байты
        mime_data.setData(MIME_NODE_TYPE, str(block_type_name).encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)


class BlockPalettePanel(QWidget):
    """
    Обёртка с заголовком, если захочешь вынести палитру отдельно.
    Сейчас в MainWindow используется напрямую BlockPalette.
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
