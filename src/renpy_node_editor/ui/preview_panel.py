from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
)
from PySide6.QtGui import QFont, QColor, QTextCursor

from renpy_node_editor.core.i18n import tr


class PreviewPanel(QWidget):
    """
    Professional preview panel with syntax highlighting support.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Применяем стиль
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                color: #E0E0E0;
            }
            QPlainTextEdit {
                background-color: #1E1E1E;
                border: 2px solid #3A3A3A;
                border-radius: 6px;
                color: #E0E0E0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                padding: 8px;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel(tr("ui.preview_panel.title", "📄 Предпросмотр Ren'Py-кода"), self)
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self._code_view = QPlainTextEdit(self)
        self._code_view.setReadOnly(True)
        self._code_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Улучшенный шрифт для кода
        code_font = QFont("Consolas", 10)
        code_font.setStyleHint(QFont.StyleHint.Monospace)
        self._code_view.setFont(code_font)
        
        layout.addWidget(self._code_view, 1)

    def set_code(self, text: str) -> None:
        self._code_view.setPlainText(text)
        # Прокручиваем в начало
        cursor = self._code_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._code_view.setTextCursor(cursor)

    def clear(self) -> None:
        self._code_view.clear()

    def append_log(self, line: str) -> None:
        cursor = self._code_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(line + "\n")
        self._code_view.setTextCursor(cursor)
        self._code_view.ensureCursorVisible()
