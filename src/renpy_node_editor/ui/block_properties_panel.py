from __future__ import annotations

from typing import Optional
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton,
    QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from renpy_node_editor.core.model import Block, BlockType


class BlockPropertiesPanel(QWidget):
    """Professional properties panel with modern design"""
    
    # Signal emitted when properties are saved
    properties_saved = Signal(object)  # emits Block

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_block: Optional[Block] = None
        self._param_widgets: dict[str, QWidget] = {}
        
        # Применяем стиль
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 10px;
                padding: 2px;
            }
            QLineEdit {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                background-color: #2F2F2F;
            }
            QTextEdit {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }
            QTextEdit:focus {
                border-color: #4A90E2;
                background-color: #2F2F2F;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 10px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #3A3A3A;
                border-radius: 3px;
                background-color: #2A2A2A;
            }
            QCheckBox::indicator:checked {
                background-color: #4A90E2;
                border-color: #6BA3F0;
            }
            QPushButton {
                background-color: #4A90E2;
                border: none;
                border-radius: 6px;
                padding: 10px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5BA0F2;
            }
            QPushButton:pressed {
                background-color: #3A80D2;
            }
            QListWidget {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                color: #E0E0E0;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                color: #FFFFFF;
            }
        """)
        
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the UI"""
        self.properties_layout = QVBoxLayout()
        self.properties_layout.setSpacing(8)
        self.properties_layout.setContentsMargins(8, 8, 8, 8)
        
        title = QLabel("⚙️ Свойства блока")
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        self.properties_layout.addWidget(title)
        
        save_button = QPushButton("💾 Сохранить свойства", self)
        save_button.clicked.connect(self._on_save)
        self.properties_layout.addWidget(save_button)
        
        self.properties_layout.addStretch()
        self.setLayout(self.properties_layout)

    def set_block(self, block: Optional[Block]) -> None:
        """Set the block to edit"""
        self.current_block = block
        self._update_properties()

    def _update_properties(self) -> None:
        """Update the properties based on block type"""
        for i in reversed(range(2, self.properties_layout.count())):
            widget = self.properties_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self._param_widgets.clear()
        
        if not self.current_block:
            return
        
        block_type = self.current_block.type
        
        if block_type == BlockType.SAY:
            self._add_text_field("who", "Персонаж:", "")
            self._add_text_field("text", "Текст:", "")
            self._add_text_field("expression", "Выражение (опционально):", "")
            self._add_text_field("at", "Позиция (опционально):", "")
            self._add_text_field("with_transition", "Переход (опционально):", "")
        elif block_type == BlockType.NARRATION:
            self._add_text_field("text", "Текст:", "")
            self._add_text_field("with_transition", "Переход (опционально):", "")
        elif block_type == BlockType.MENU:
            self._add_text_field("question", "Вопрос:", "")
            self._add_menu_choices()
        elif block_type == BlockType.IF:
            self._add_text_field("condition", "Условие:", "variable == True")
        elif block_type == BlockType.WHILE:
            self._add_text_field("condition", "Условие:", "True")
        elif block_type == BlockType.FOR:
            self._add_text_field("variable", "Переменная:", "i")
            self._add_text_field("iterable", "Итерируемый объект:", "[1, 2, 3]")
        elif block_type == BlockType.JUMP:
            self._add_text_field("target", "Переход на метку:", "")
        elif block_type == BlockType.CALL:
            self._add_text_field("label", "Вызов метки:", "")
        elif block_type == BlockType.PAUSE:
            self._add_text_field("duration", "Длительность (сек):", "1.0")
        elif block_type == BlockType.TRANSITION:
            self._add_text_field("transition", "Название перехода:", "dissolve")
        elif block_type == BlockType.WITH:
            self._add_text_field("transition", "Название перехода:", "dissolve")
        elif block_type == BlockType.SOUND:
            self._add_text_field("sound_file", "Файл звука:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
            self._add_checkbox("loop", "Зациклить", False)
        elif block_type == BlockType.MUSIC:
            self._add_text_field("music_file", "Файл музыки:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
            self._add_checkbox("loop", "Зациклить", True)
        elif block_type == BlockType.STOP_MUSIC:
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
        elif block_type == BlockType.STOP_SOUND:
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
        elif block_type == BlockType.QUEUE_MUSIC:
            self._add_text_field("music_file", "Файл музыки:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
            self._add_checkbox("loop", "Зациклить", False)
        elif block_type == BlockType.QUEUE_SOUND:
            self._add_text_field("sound_file", "Файл звука:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
        elif block_type == BlockType.SET_VAR:
            self._add_text_field("variable", "Имя переменной:", "")
            self._add_text_field("value", "Значение:", "")
        elif block_type == BlockType.DEFAULT:
            self._add_text_field("variable", "Имя переменной:", "")
            self._add_text_field("value", "Значение по умолчанию:", "")
        elif block_type == BlockType.DEFINE:
            self._add_text_field("name", "Имя константы:", "")
            self._add_text_field("value", "Значение:", "")
        elif block_type == BlockType.PYTHON:
            self._add_code_field("code", "Python код:")
        elif block_type == BlockType.CHARACTER:
            self._add_text_field("name", "Имя персонажа:", "")
            self._add_text_field("display_name", "Отображаемое имя:", "")
        elif block_type == BlockType.IMAGE:
            self._add_text_field("name", "Имя изображения:", "")
            self._add_text_field("path", "Путь к файлу:", "")
        elif block_type == BlockType.LABEL:
            self._add_text_field("label", "Имя метки:", "")
        elif block_type == BlockType.SCENE:
            self._add_text_field("background", "Фон:", "black")
            self._add_text_field("layer", "Слой (опционально):", "")
            self._add_text_field("transition", "Переход (опционально):", "")
        elif block_type == BlockType.SHOW:
            self._add_text_field("character", "Персонаж/Изображение:", "")
            self._add_text_field("expression", "Выражение (опционально):", "")
            self._add_text_field("at", "Позиция (опционально):", "")
            self._add_text_field("behind", "Behind (опционально):", "")
            self._add_text_field("zorder", "Z-order (опционально):", "")
            self._add_text_field("layer", "Слой (опционально):", "")
            self._add_text_field("transition", "Переход (опционально):", "")
        elif block_type == BlockType.HIDE:
            self._add_text_field("character", "Персонаж:", "")
            self._add_text_field("layer", "Слой (опционально):", "")
            self._add_text_field("transition", "Переход (опционально):", "")
        elif block_type == BlockType.VOICE:
            self._add_text_field("voice_file", "Файл голоса:", "")
        elif block_type == BlockType.CENTER:
            self._add_text_field("text", "Текст:", "")
        elif block_type == BlockType.TEXT:
            self._add_text_field("text", "Текст:", "")
            self._add_text_field("xpos", "X позиция (опционально):", "")
            self._add_text_field("ypos", "Y позиция (опционально):", "")
        elif block_type == BlockType.RETURN:
            # RETURN has no parameters
            pass

    def _add_text_field(self, key: str, label: str, default: str = "") -> None:
        """Add a text input field for a parameter."""
        label_widget = QLabel(label, self)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        input_widget = QLineEdit(self)
        value = self.current_block.params.get(key, default) if self.current_block else default
        input_widget.setText(str(value))
        self._param_widgets[key] = input_widget
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, input_widget)

    def _add_code_field(self, key: str, label: str) -> None:
        """Add a multi-line code input field"""
        label_widget = QLabel(label, self)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        code_widget = QTextEdit(self)
        code_widget.setMaximumHeight(150)
        value = self.current_block.params.get(key, "") if self.current_block else ""
        code_widget.setPlainText(str(value))
        self._param_widgets[key] = code_widget
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, code_widget)

    def _add_checkbox(self, key: str, label: str, default: bool = False) -> None:
        """Add a checkbox for a boolean parameter."""
        checkbox = QCheckBox(label, self)
        value = self.current_block.params.get(key, default) if self.current_block else default
        if isinstance(value, str):
            value = value.lower() in ("true", "1", "yes", "on")
        checkbox.setChecked(bool(value))
        self._param_widgets[key] = checkbox
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, checkbox)

    def _add_menu_choices(self) -> None:
        """Add UI for managing menu choices"""
        choices_label = QLabel("Варианты меню:", self)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_label)
        
        choices_list = QListWidget(self)
        choices_list.setMaximumHeight(150)
        
        choices = self.current_block.params.get("choices", [])
        if isinstance(choices, str):
            try:
                choices = json.loads(choices)
            except:
                choices = []
        elif not isinstance(choices, list):
            choices = []
        
        for choice in choices:
            if isinstance(choice, dict):
                text = choice.get("text", "")
                jump = choice.get("jump", "")
                condition = choice.get("condition", "")
                item_text = f"{text}"
                if jump:
                    item_text += f" → {jump}"
                if condition:
                    item_text += f" [if {condition}]"
            else:
                item_text = str(choice)
            choices_list.addItem(item_text)
        
        self._param_widgets["_choices_list"] = choices_list
        self._param_widgets["_choices_data"] = choices
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_list)
        
        choices_buttons = QHBoxLayout()
        choices_buttons.setSpacing(4)
        
        add_btn = QPushButton("➕ Добавить", self)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #70AD47;
                font-size: 9px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #8FC966;
            }
        """)
        add_btn.clicked.connect(lambda: self._add_menu_choice(choices_list))
        choices_buttons.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Изменить", self)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8C00;
                font-size: 9px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #FFA533;
            }
        """)
        edit_btn.clicked.connect(lambda: self._edit_menu_choice(choices_list))
        choices_buttons.addWidget(edit_btn)
        
        remove_btn = QPushButton("➖ Удалить", self)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                font-size: 9px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #FF8E8E;
            }
        """)
        remove_btn.clicked.connect(lambda: self._remove_menu_choice(choices_list))
        choices_buttons.addWidget(remove_btn)
        
        choices_widget = QWidget(self)
        choices_widget.setLayout(choices_buttons)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_widget)

    def _add_menu_choice(self, choices_list: QListWidget) -> None:
        """Add a new menu choice"""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok1 = QInputDialog.getText(self, "Вариант меню", "Текст варианта:")
        if not ok1 or not text:
            return
        
        jump, ok2 = QInputDialog.getText(self, "Вариант меню", "Переход на метку (опционально):")
        if not ok2:
            return
        
        condition, ok3 = QInputDialog.getText(self, "Вариант меню", "Условие (опционально):")
        if not ok3:
            return
        
        choice = {"text": text, "jump": jump, "condition": condition}
        choices_data = self._param_widgets.get("_choices_data", [])
        choices_data.append(choice)
        self._param_widgets["_choices_data"] = choices_data
        
        item_text = f"{text}"
        if jump:
            item_text += f" → {jump}"
        if condition:
            item_text += f" [if {condition}]"
        choices_list.addItem(item_text)

    def _edit_menu_choice(self, choices_list: QListWidget) -> None:
        """Edit selected menu choice"""
        current_item = choices_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Нет выбора", "Выберите вариант для редактирования.")
            return
        
        index = choices_list.row(current_item)
        choices_data = self._param_widgets.get("_choices_data", [])
        
        if index < len(choices_data):
            choice = choices_data[index]
            if isinstance(choice, dict):
                text = choice.get("text", "")
                jump = choice.get("jump", "")
                condition = choice.get("condition", "")
            else:
                text = str(choice)
                jump = ""
                condition = ""
            
            from PySide6.QtWidgets import QInputDialog
            
            new_text, ok1 = QInputDialog.getText(self, "Редактировать вариант", "Текст варианта:", text=text)
            if not ok1:
                return
            
            new_jump, ok2 = QInputDialog.getText(self, "Редактировать вариант", "Переход на метку (опционально):", text=jump)
            if not ok2:
                return
            
            new_condition, ok3 = QInputDialog.getText(self, "Редактировать вариант", "Условие (опционально):", text=condition)
            if not ok3:
                return
            
            choices_data[index] = {"text": new_text, "jump": new_jump, "condition": new_condition}
            self._param_widgets["_choices_data"] = choices_data
            
            item_text = f"{new_text}"
            if new_jump:
                item_text += f" → {new_jump}"
            if new_condition:
                item_text += f" [if {new_condition}]"
            current_item.setText(item_text)

    def _remove_menu_choice(self, choices_list: QListWidget) -> None:
        """Remove selected menu choice"""
        current_item = choices_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Нет выбора", "Выберите вариант для удаления.")
            return
        
        index = choices_list.row(current_item)
        choices_data = self._param_widgets.get("_choices_data", [])
        
        if index < len(choices_data):
            choices_data.pop(index)
            self._param_widgets["_choices_data"] = choices_data
        
        choices_list.takeItem(index)

    def _on_save(self) -> None:
        """Save all parameter changes back to the block."""
        if not self.current_block:
            return
        
        for key, widget in self._param_widgets.items():
            if key.startswith("_"):
                continue
            
            if isinstance(widget, QLineEdit):
                self.current_block.params[key] = widget.text()
            elif isinstance(widget, QTextEdit):
                self.current_block.params[key] = widget.toPlainText()
            elif isinstance(widget, QCheckBox):
                self.current_block.params[key] = widget.isChecked()
        
        # Сохраняем варианты меню
        if "_choices_data" in self._param_widgets:
            choices_data = self._param_widgets["_choices_data"]
            self.current_block.params["choices"] = choices_data
        
        # Emit signal to notify that properties were saved
        self.properties_saved.emit(self.current_block)
