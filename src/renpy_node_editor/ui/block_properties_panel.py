from __future__ import annotations

from typing import Optional
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton,
    QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from renpy_node_editor.core.model import Block, BlockType


class BlockPropertiesPanel(QWidget):
    """Panel for editing block properties"""
    
    # Signal emitted when properties are saved
    properties_saved = Signal(object)  # emits Block

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_block: Optional[Block] = None
        self._param_widgets: dict[str, QWidget] = {}
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the UI"""
        self.properties_layout = QVBoxLayout()
        
        title = QLabel("Block Properties")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.properties_layout.addWidget(title)
        
        save_button = QPushButton("Save Properties")
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
        
        if self.current_block.type == BlockType.SAY:
            self._add_text_field("who", "Character:", "")
            self._add_text_field("text", "Text:", "")
        elif self.current_block.type == BlockType.NARRATION:
            self._add_text_field("text", "Text:", "")
        elif self.current_block.type == BlockType.MENU:
            self._add_text_field("question", "Question:", "")
            self._add_menu_choices()
        elif self.current_block.type == BlockType.IF:
            self._add_text_field("condition", "Condition:", "variable == True")
        elif self.current_block.type == BlockType.JUMP:
            self._add_text_field("target", "Jump to Label:", "")
        elif self.current_block.type == BlockType.CALL:
            self._add_text_field("label", "Call Label:", "")
        elif self.current_block.type == BlockType.PAUSE:
            self._add_text_field("duration", "Duration (seconds):", "1.0")
        elif self.current_block.type == BlockType.TRANSITION:
            self._add_text_field("transition", "Transition Name:", "fade")
            self._add_text_field("duration", "Duration:", "1.0")
        elif self.current_block.type == BlockType.SOUND:
            self._add_text_field("sound_file", "Sound File:", "")
        elif self.current_block.type == BlockType.MUSIC:
            self._add_text_field("music_file", "Music File:", "")
            self._add_checkbox("loop", "Loop music", True)
        elif self.current_block.type == BlockType.SET_VAR:
            self._add_text_field("variable", "Variable Name:", "")
            self._add_text_field("value", "Value:", "")
        elif self.current_block.type == BlockType.LABEL:
            self._add_text_field("label", "Label Name:", "")
        elif self.current_block.type == BlockType.SCENE:
            self._add_text_field("background", "Background:", "black")
            self._add_text_field("transition", "Transition (optional):", "")
        elif self.current_block.type == BlockType.SHOW:
            self._add_text_field("character", "Character:", "")
            self._add_text_field("expression", "Expression (optional):", "")
            self._add_text_field("at", "At (optional):", "")
        elif self.current_block.type == BlockType.HIDE:
            self._add_text_field("character", "Character:", "")
        elif self.current_block.type == BlockType.RETURN:
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
        choices_label = QLabel("Menu Choices:", self)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_label)
        
        # List widget для отображения вариантов
        choices_list = QListWidget(self)
        choices_list.setMaximumHeight(150)
        
        # Загружаем существующие варианты
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
                item_text = f"{text} → {jump}" if jump else text
            else:
                item_text = str(choice)
            choices_list.addItem(item_text)
        
        self._param_widgets["_choices_list"] = choices_list
        self._param_widgets["_choices_data"] = choices
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_list)
        
        # Кнопки управления
        choices_buttons = QHBoxLayout()
        
        add_btn = QPushButton("Add Choice", self)
        add_btn.clicked.connect(lambda: self._add_menu_choice(choices_list))
        choices_buttons.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit", self)
        edit_btn.clicked.connect(lambda: self._edit_menu_choice(choices_list))
        choices_buttons.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove", self)
        remove_btn.clicked.connect(lambda: self._remove_menu_choice(choices_list))
        choices_buttons.addWidget(remove_btn)
        
        choices_widget = QWidget(self)
        choices_widget.setLayout(choices_buttons)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_widget)

    def _add_menu_choice(self, choices_list: QListWidget) -> None:
        """Add a new menu choice"""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok1 = QInputDialog.getText(self, "Menu Choice", "Choice text:")
        if not ok1 or not text:
            return
        
        jump, ok2 = QInputDialog.getText(self, "Menu Choice", "Jump to label (optional):")
        if not ok2:
            return
        
        choice = {"text": text, "jump": jump}
        choices_data = self._param_widgets.get("_choices_data", [])
        choices_data.append(choice)
        self._param_widgets["_choices_data"] = choices_data
        
        item_text = f"{text} → {jump}" if jump else text
        choices_list.addItem(item_text)

    def _edit_menu_choice(self, choices_list: QListWidget) -> None:
        """Edit selected menu choice"""
        current_item = choices_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a choice to edit.")
            return
        
        index = choices_list.row(current_item)
        choices_data = self._param_widgets.get("_choices_data", [])
        
        if index < len(choices_data):
            choice = choices_data[index]
            if isinstance(choice, dict):
                text = choice.get("text", "")
                jump = choice.get("jump", "")
            else:
                text = str(choice)
                jump = ""
            
            from PySide6.QtWidgets import QInputDialog
            
            new_text, ok1 = QInputDialog.getText(self, "Edit Choice", "Choice text:", text=text)
            if not ok1:
                return
            
            new_jump, ok2 = QInputDialog.getText(self, "Edit Choice", "Jump to label (optional):", text=jump)
            if not ok2:
                return
            
            choices_data[index] = {"text": new_text, "jump": new_jump}
            self._param_widgets["_choices_data"] = choices_data
            
            item_text = f"{new_text} → {new_jump}" if new_jump else new_text
            current_item.setText(item_text)

    def _remove_menu_choice(self, choices_list: QListWidget) -> None:
        """Remove selected menu choice"""
        current_item = choices_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a choice to remove.")
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
                continue  # Пропускаем служебные виджеты
            
            if isinstance(widget, QLineEdit):
                self.current_block.params[key] = widget.text()
            elif isinstance(widget, QCheckBox):
                self.current_block.params[key] = widget.isChecked()
        
        # Сохраняем варианты меню
        if "_choices_data" in self._param_widgets:
            choices_data = self._param_widgets["_choices_data"]
            self.current_block.params["choices"] = choices_data
        
        # Emit signal to notify that properties were saved
        self.properties_saved.emit(self.current_block)
