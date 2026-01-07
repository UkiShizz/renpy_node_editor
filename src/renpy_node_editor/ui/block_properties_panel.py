from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton
from PyQt6.QtCore import Qt
from enum import Enum


class BlockType(Enum):
    """Enumeration of block types"""
    SAY = "say"
    MENU = "menu"
    IF = "if"
    JUMP = "jump"
    CALL = "call"
    PAUSE = "pause"
    TRANSITION = "transition"
    SOUND = "sound"
    MUSIC = "music"
    SET_VAR = "set_var"
    LABEL = "label"


class BlockPropertiesPanel(QWidget):
    """Panel for editing block properties"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_block = None
        self._param_widgets = {}
        self.init_ui()

    def init_ui(self):
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

    def set_block(self, block):
        """Set the block to edit"""
        self.current_block = block
        self._update_properties()

    def _update_properties(self):
        """Update the properties based on block type"""
        for i in reversed(range(2, self.properties_layout.count())):
            widget = self.properties_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self._param_widgets.clear()
        
        if not self.current_block:
            return
        
        if self.current_block.type == BlockType.SAY:
            self._add_text_field("character", "Character:", "")
            self._add_text_field("text", "Text:", "")
        elif self.current_block.type == BlockType.MENU:
            self._add_text_field("prompt", "Prompt Text:", "What do you choose?")
            self._add_text_field("options", "Options (comma-separated):", "Option 1, Option 2")
        elif self.current_block.type == BlockType.IF:
            self._add_text_field("condition", "Condition:", "variable == True")
        elif self.current_block.type == BlockType.JUMP:
            self._add_text_field("label", "Jump to Label:", "")
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
            self._add_text_field("loop", "Loop:", "True")
        elif self.current_block.type == BlockType.SET_VAR:
            self._add_text_field("variable", "Variable Name:", "")
            self._add_text_field("value", "Value:", "")
        elif self.current_block.type == BlockType.LABEL:
            self._add_text_field("label_name", "Label Name:", "")

    def _add_text_field(self, key: str, label: str, default: str = "") -> None:
        """Add a text input field for a parameter."""
        label_widget = QLabel(label, self)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        input_widget = QLineEdit(self)
        value = self.current_block.params.get(key, default) if self.current_block else default
        input_widget.setText(str(value))
        self._param_widgets[key] = input_widget
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, input_widget)

    def _on_save(self) -> None:
        """Save all parameter changes back to the block."""
        if not self.current_block:
            return
        
        for key, widget in self._param_widgets.items():
            if isinstance(widget, QLineEdit):
                self.current_block.params[key] = widget.text()
            elif isinstance(widget, QCheckBox):
                self.current_block.params[key] = widget.isChecked()
        
        print(f"Block {self.current_block.id} properties saved: {self.current_block.params}")
