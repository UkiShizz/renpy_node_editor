from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
)


class PreviewPanel(QWidget):
    """
    Панель предпросмотра Ren'Py-кода и (при желании) логов.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("Предпросмотр Ren'Py-кода", self)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self._code_view = QPlainTextEdit(self)
        self._code_view.setReadOnly(True)
        self._code_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(self._code_view, 1)

    def set_code(self, text: str) -> None:
        self._code_view.setPlainText(text)

    def clear(self) -> None:
        self._code_view.clear()

    def append_log(self, line: str) -> None:
        cursor = self._code_view.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(line + "\n")
        self._code_view.setTextCursor(cursor)
        self._code_view.ensureCursorVisible()
