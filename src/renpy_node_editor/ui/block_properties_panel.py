from __future__ import annotations

from typing import Optional, Dict
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton,
    QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QTextEdit, QComboBox,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from renpy_node_editor.core.model import Block, BlockType, Project
from renpy_node_editor.ui.tooltips import (
    get_parameter_tooltip,
    get_transition_tooltip,
    get_position_tooltip,
    get_layer_tooltip,
    get_background_tooltip,
)

# Стандартные переходы Ren'Py (https://www.renpy.org/doc/html/transitions.html)
RENPY_TRANSITIONS = [
    "dissolve", "fade", "pixellate", "move",
    "moveinleft", "moveinright", "moveintop", "moveinbottom",
    "moveoutleft", "moveoutright", "moveouttop", "moveoutbottom",
    "zoomin", "zoomout", "vpunch", "hpunch",
    "blinds", "squares",
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "slideup", "slidedown",
    "pushleft", "pushright", "pushup", "pushdown",
    "irisin", "irisout", "circleirisin", "circleirisout",
    "circlewipe", "alphadissolve", "size", "push", "pull"
]

# Стандартные позиции для at (https://www.renpy.org/doc/html/displaying_images.html#position-transforms)
RENPY_POSITIONS = [
    "left", "right", "center", "truecenter",
    "topleft", "topright", "topcenter",
    "bottomleft", "bottomright", "bottomcenter"
]

# Стандартные слои Ren'Py (https://www.renpy.org/doc/html/displaying_images.html#layers)
RENPY_LAYERS = [
    "master", "transient", "screens", "overlay"
]

# Стандартные фоны для scene
RENPY_BACKGROUNDS = [
    "black", "white"
]

# Поддерживаемые форматы аудио файлов
AUDIO_FORMATS = [
    ".ogg", ".mp3", ".wav", ".opus"
]

# Поддерживаемые форматы изображений
IMAGE_FORMATS = [
    ".png", ".jpg", ".jpeg", ".webp", ".gif"
]

# Типы данных для переменных
VARIABLE_TYPES = [
    "int", "float", "str", "bool", "list", "dict"
]


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
        save_button.setToolTip("Сохранить изменения в свойствах блока")
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
            self._add_character_field("who", "Персонаж:", "")
            self._add_text_field("text", "Текст:", "")
            self._add_text_field("expression", "Выражение (опционально):", "")
            self._add_combo_field("at", "Позиция (опционально):", RENPY_POSITIONS, "")
            self._add_combo_field("with_transition", "Переход (опционально):", RENPY_TRANSITIONS, "")
        elif block_type == BlockType.NARRATION:
            self._add_text_field("text", "Текст:", "")
            self._add_combo_field("with_transition", "Переход (опционально):", RENPY_TRANSITIONS, "")
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
            self._add_combo_field("transition", "Название перехода:", RENPY_TRANSITIONS, "dissolve")
        elif block_type == BlockType.WITH:
            self._add_combo_field("transition", "Название перехода:", RENPY_TRANSITIONS, "dissolve")
        elif block_type == BlockType.SOUND:
            self._add_audio_file_field("sound_file", "Файл звука:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
            self._add_checkbox("loop", "Зациклить", False)
        elif block_type == BlockType.MUSIC:
            self._add_audio_file_field("music_file", "Файл музыки:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
            self._add_checkbox("loop", "Зациклить", True)
        elif block_type == BlockType.STOP_MUSIC:
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
        elif block_type == BlockType.STOP_SOUND:
            self._add_text_field("fadeout", "Fade out (сек, опционально):", "")
        elif block_type == BlockType.QUEUE_MUSIC:
            self._add_audio_file_field("music_file", "Файл музыки:", "")
            self._add_text_field("fadein", "Fade in (сек, опционально):", "")
            self._add_checkbox("loop", "Зациклить", False)
        elif block_type == BlockType.QUEUE_SOUND:
            self._add_audio_file_field("sound_file", "Файл звука:", "")
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
            self._add_file_field("path", "Путь к файлу:", "", "image")
        elif block_type == BlockType.LABEL:
            self._add_text_field("label", "Имя метки:", "")
        elif block_type == BlockType.START:
            # START блок имеет свой собственный label, чтобы на него могли ссылаться JUMP и CALL
            self._add_text_field("label", "Имя метки (label):", "")
        elif block_type == BlockType.SCENE:
            # Фон может быть "black", "white" или имя изображения (например, "bg room")
            # Добавляем поле с кнопкой выбора файла
            self._add_background_field("background", "Фон:", "black")
            self._add_combo_field("layer", "Слой (опционально):", RENPY_LAYERS, "")
            self._add_combo_field("transition", "Переход (опционально):", RENPY_TRANSITIONS, "")
        elif block_type == BlockType.SHOW:
            self._add_character_or_image_field("character", "Персонаж/Изображение:", "")
            self._add_text_field("expression", "Выражение (опционально):", "")
            self._add_combo_field("at", "Позиция (опционально):", RENPY_POSITIONS, "")
            self._add_text_field("behind", "Behind (опционально):", "")
            self._add_text_field("zorder", "Z-order (опционально):", "")
            self._add_combo_field("layer", "Слой (опционально):", RENPY_LAYERS, "")
            self._add_combo_field("transition", "Переход (опционально):", RENPY_TRANSITIONS, "")
        elif block_type == BlockType.HIDE:
            self._add_character_or_image_field("character", "Персонаж/Изображение:", "")
            self._add_combo_field("layer", "Слой (опционально):", RENPY_LAYERS, "")
            self._add_combo_field("transition", "Переход (опционально):", RENPY_TRANSITIONS, "")
        elif block_type == BlockType.VOICE:
            self._add_audio_file_field("voice_file", "Файл голоса:", "")
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
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        input_widget = QLineEdit(self)
        value = self.current_block.params.get(key, default) if self.current_block else default
        input_widget.setText(str(value))
        input_widget.setToolTip(tooltip)
        self._param_widgets[key] = input_widget
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, input_widget)

    def _add_background_field(self, key: str, label: str, default: str = "") -> None:
        """Add a background field with combo box and file browse button"""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        # Контейнер для комбобокса и кнопки
        bg_container = QHBoxLayout()
        bg_container.setSpacing(4)
        
        # Комбобокс с предопределенными значениями и возможностью ввода
        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItem("")  # Пустой вариант
        combo.addItems(RENPY_BACKGROUNDS)
        
        # Добавляем определенные изображения из проекта
        defined_images = self._get_defined_images()
        if defined_images:
            combo.addItem("--- Определенные изображения ---")
            for image_name in sorted(defined_images.keys()):
                combo.addItem(image_name)
        
        value = self.current_block.params.get(key, default) if self.current_block else default
        current_text = str(value) if value else ""
        
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(current_text)
        
        combo.setToolTip(tooltip)
        combo.setStyleSheet(self._get_combo_style())
        
        # Добавляем tooltips к пунктам фона
        for i in range(combo.count()):
            item_text = combo.itemText(i)
            if item_text and not item_text.startswith("---"):
                item_tooltip = get_background_tooltip(item_text)
                combo.setItemData(i, item_tooltip, Qt.ToolTipRole)
        
        # Подключаем сигнал для отображения tooltip при наведении на пункты
        def on_highlighted(index: int) -> None:
            tooltip_text = combo.itemData(index, Qt.ToolTipRole)
            if tooltip_text:
                combo.setToolTip(str(tooltip_text))
            else:
                combo.setToolTip(tooltip)
        
        combo.highlighted.connect(on_highlighted)
        
        self._param_widgets[key] = combo
        bg_container.addWidget(combo, 1)
        
        # Кнопка выбора файла
        browse_btn = QPushButton("📁", self)
        browse_btn.setToolTip("Выбрать файл изображения")
        browse_btn.setMaximumWidth(40)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                font-size: 12px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #5BA0F2;
            }
            QPushButton:pressed {
                background-color: #3A80D2;
            }
        """)
        
        def on_browse_clicked():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"Выбрать изображение для {label}",
                "",
                "Изображения (*.png *.jpg *.jpeg *.webp *.gif);;Все файлы (*.*)"
            )
            if file_path:
                from pathlib import Path
                filename = Path(file_path).stem
                # Предлагаем имя в формате "bg filename"
                suggested_name = f"bg {filename}" if not filename.startswith("bg ") else filename
                combo.setCurrentText(suggested_name)
        
        browse_btn.clicked.connect(on_browse_clicked)
        bg_container.addWidget(browse_btn)
        
        bg_widget = QWidget(self)
        bg_widget.setLayout(bg_container)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, bg_widget)

    def _add_file_field(self, key: str, label: str, default: str = "", file_type: str = "all") -> None:
        """Add a file path input field with a browse button."""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        # Контейнер для поля ввода и кнопки
        file_container = QHBoxLayout()
        file_container.setSpacing(4)
        
        input_widget = QLineEdit(self)
        value = self.current_block.params.get(key, default) if self.current_block else default
        input_widget.setText(str(value))
        input_widget.setToolTip(tooltip)
        self._param_widgets[key] = input_widget
        file_container.addWidget(input_widget, 1)
        
        # Кнопка выбора файла
        browse_btn = QPushButton("📁", self)
        browse_btn.setToolTip("Выбрать файл")
        browse_btn.setMaximumWidth(40)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                font-size: 12px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #5BA0F2;
            }
            QPushButton:pressed {
                background-color: #3A80D2;
            }
        """)
        
        # Определяем фильтры файлов в зависимости от типа
        if file_type == "audio":
            file_filter = "Аудио файлы (*.ogg *.mp3 *.wav *.opus);;Все файлы (*.*)"
        elif file_type == "image":
            file_filter = "Изображения (*.png *.jpg *.jpeg *.webp *.gif);;Все файлы (*.*)"
        else:
            file_filter = "Все файлы (*.*)"
        
        def on_browse_clicked():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"Выбрать файл для {label}",
                "",
                file_filter
            )
            if file_path:
                input_widget.setText(file_path)
        
        browse_btn.clicked.connect(on_browse_clicked)
        file_container.addWidget(browse_btn)
        
        file_widget = QWidget(self)
        file_widget.setLayout(file_container)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, file_widget)

    def _add_code_field(self, key: str, label: str) -> None:
        """Add a multi-line code input field"""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        code_widget = QTextEdit(self)
        code_widget.setMaximumHeight(150)
        value = self.current_block.params.get(key, "") if self.current_block else ""
        code_widget.setPlainText(str(value))
        code_widget.setToolTip(tooltip)
        self._param_widgets[key] = code_widget
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, code_widget)

    def _add_checkbox(self, key: str, label: str, default: bool = False) -> None:
        """Add a checkbox for a boolean parameter."""
        checkbox = QCheckBox(label, self)
        value = self.current_block.params.get(key, default) if self.current_block else default
        if isinstance(value, str):
            value = value.lower() in ("true", "1", "yes", "on")
        checkbox.setChecked(bool(value))
        tooltip = get_parameter_tooltip(key)
        checkbox.setToolTip(tooltip)
        self._param_widgets[key] = checkbox
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, checkbox)
    
    def _get_combo_style(self) -> str:
        """Возвращает стиль для QComboBox (вынесено для переиспользования)"""
        return """
            QComboBox {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                color: #E0E0E0;
                padding: 4px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #4A90E2;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #E0E0E0;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                color: #E0E0E0;
                selection-background-color: #4A90E2;
                selection-color: #FFFFFF;
            }
        """
    
    def _add_combo_field(self, key: str, label: str, options: list[str], default: str = "") -> None:
        """Add a combo box (dropdown) for a parameter with predefined options."""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        combo = QComboBox(self)
        combo.setEditable(True)  # Разрешаем ввод своего значения
        combo.addItem("")  # Пустой вариант для опциональных полей
        
        # Добавляем опции с tooltips
        for option in options:
            combo.addItem(option)
            # Определяем tooltip в зависимости от типа поля
            if key == "with_transition" or key == "transition":
                item_tooltip = get_transition_tooltip(option)
            elif key == "at":
                item_tooltip = get_position_tooltip(option)
            elif key == "layer":
                item_tooltip = get_layer_tooltip(option)
            elif key == "background":
                item_tooltip = get_background_tooltip(option)
            else:
                item_tooltip = f"{option}"
            
            # Устанавливаем tooltip через setItemData
            combo.setItemData(combo.count() - 1, item_tooltip, Qt.ToolTipRole)
        
        # Устанавливаем текущее значение
        value = self.current_block.params.get(key, default) if self.current_block else default
        current_text = str(value) if value else ""
        
        # Ищем в списке
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            # Если значения нет в списке, устанавливаем его как текущий текст
            combo.setCurrentText(current_text)
        
        combo.setToolTip(tooltip)
        combo.setStyleSheet(self._get_combo_style())
        
        # Подключаем сигнал для отображения tooltip при наведении на пункты
        def on_highlighted(index: int) -> None:
            tooltip_text = combo.itemData(index, Qt.ToolTipRole)
            if tooltip_text:
                combo.setToolTip(str(tooltip_text))
            else:
                combo.setToolTip(tooltip)
        
        combo.highlighted.connect(on_highlighted)
        
        self._param_widgets[key] = combo
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, combo)

    def _add_menu_choices(self) -> None:
        """Add UI for managing menu choices"""
        choices_label = QLabel("Варианты меню:", self)
        choices_label.setToolTip("Список вариантов выбора для меню. Каждый вариант может иметь текст, переход и условие.")
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, choices_label)
        
        choices_list = QListWidget(self)
        choices_list.setMaximumHeight(150)
        
        choices = self.current_block.params.get("choices", [])
        if isinstance(choices, str):
            try:
                choices = json.loads(choices)
            except (json.JSONDecodeError, ValueError):
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
            elif isinstance(widget, QComboBox):
                # Для комбобокса берем текущий текст (может быть выбран из списка или введен вручную)
                text = widget.currentText().strip()
                # Сохраняем пустую строку вместо None для пустых значений
                self.current_block.params[key] = text if text else ""
        
        # Сохраняем варианты меню
        if "_choices_data" in self._param_widgets:
            choices_data = self._param_widgets["_choices_data"]
            self.current_block.params["choices"] = choices_data
        
        # Emit signal to notify that properties were saved
        self.properties_saved.emit(self.current_block)
    
    def _get_current_scene(self):
        """Получить текущую сцену"""
        # Пытаемся получить сцену через parent
        parent = self.parent()
        while parent:
            if hasattr(parent, 'node_view'):
                node_view = parent.node_view
                if hasattr(node_view, 'node_scene'):
                    scene = node_view.node_scene
                    if hasattr(scene, '_scene_model'):
                        return scene._scene_model
            parent = parent.parent()
        return None
    
    def _get_project(self) -> Optional[Project]:
        """Получить текущий проект"""
        parent = self.parent()
        while parent:
            if hasattr(parent, '_controller'):
                controller = parent._controller
                if hasattr(controller, 'project'):
                    return controller.project
            parent = parent.parent()
        return None
    
    def _get_scene_labels(self) -> list[str]:
        """Получить список лейблов из всех сцен проекта"""
        project = self._get_project()
        if not project:
            return []
        
        labels = []
        for scene in project.scenes:
            if scene.label and scene.label not in labels:
                labels.append(scene.label)
        
        return sorted(labels)
    
    def _add_scene_label_field(self, key: str, label: str, default: str = "") -> None:
        """Add a scene label field with combo box showing all scene labels from project"""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        # Combo box с лейблами из проекта
        combo = QComboBox(self)
        combo.setEditable(True)  # Разрешаем ввод произвольного лейбла
        combo.addItem("")  # Пустой вариант
        
        # Добавляем лейблы из всех сцен проекта
        scene_labels = self._get_scene_labels()
        if scene_labels:
            combo.addItem("--- Лейблы из проекта ---")
            for label_name in scene_labels:
                combo.addItem(label_name)
        
        value = self.current_block.params.get(key, default) if self.current_block else default
        current_text = str(value) if value else ""
        
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(current_text)
        
        combo.setToolTip(tooltip)
        combo.setStyleSheet(self._get_combo_style())
        
        self._param_widgets[key] = combo
    
    def _get_defined_images(self) -> Dict[str, str]:
        """Получить список определенных изображений из проекта"""
        project = self._get_project()
        if not project:
            return {}
        
        images: Dict[str, str] = {}
        
        # Извлекаем из IMAGE блоков
        from renpy_node_editor.core.generator.blocks import safe_get_str
        from renpy_node_editor.core.generator.main import normalize_variable_name
        
        for scene in project.scenes:
            for block in scene.blocks:
                if block.type == BlockType.IMAGE:
                    name = safe_get_str(block.params, "name")
                    path = safe_get_str(block.params, "path")
                    if name and path:
                        normalized_name = normalize_variable_name(name)
                        images[normalized_name] = path
        
        # Добавляем из project.images
        if project.images:
            for name, path in project.images.items():
                if name not in images:
                    images[name] = path
        
        return images
    
    def _get_defined_characters(self) -> list[str]:
        """Получить список определенных персонажей из проекта"""
        project = self._get_project()
        if not project:
            return []
        
        characters: set[str] = set()
        
        # Из глобальных определений
        for char_name in project.characters.keys():
            characters.add(char_name)
        
        # Из CHARACTER блоков
        from renpy_node_editor.core.generator.blocks import safe_get_str
        
        for scene in project.scenes:
            for block in scene.blocks:
                if block.type == BlockType.CHARACTER:
                    name = safe_get_str(block.params, "name")
                    if name:
                        characters.add(name)
        
        return sorted(characters)
    
    def _get_defined_audio_files(self) -> list[str]:
        """Получить список определенных аудио файлов из проекта"""
        project = self._get_project()
        if not project:
            return []
        
        audio_files: set[str] = set()
        
        # Извлекаем из блоков SOUND, MUSIC, QUEUE_SOUND, QUEUE_MUSIC, VOICE
        from renpy_node_editor.core.generator.blocks import safe_get_str
        
        for scene in project.scenes:
            for block in scene.blocks:
                if block.type in (BlockType.SOUND, BlockType.QUEUE_SOUND):
                    file_path = safe_get_str(block.params, "sound_file")
                    if file_path:
                        audio_files.add(file_path)
                elif block.type in (BlockType.MUSIC, BlockType.QUEUE_MUSIC):
                    file_path = safe_get_str(block.params, "music_file")
                    if file_path:
                        audio_files.add(file_path)
                elif block.type == BlockType.VOICE:
                    file_path = safe_get_str(block.params, "voice_file")
                    if file_path:
                        audio_files.add(file_path)
        
        return sorted(audio_files)
    
    def _add_character_field(self, key: str, label: str, default: str = "") -> None:
        """Add a combo field for selecting a character"""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItem("")  # Пустой вариант
        
        # Добавляем определенных персонажей
        defined_characters = self._get_defined_characters()
        if defined_characters:
            for char_name in defined_characters:
                combo.addItem(char_name)
        
        value = self.current_block.params.get(key, default) if self.current_block else default
        current_text = str(value) if value else ""
        
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(current_text)
        
        combo.setToolTip(tooltip)
        combo.setStyleSheet(self._get_combo_style())
        
        self._param_widgets[key] = combo
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, combo)
    
    def _add_character_or_image_field(self, key: str, label: str, default: str = "") -> None:
        """Add a combo field for selecting a character or image"""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItem("")  # Пустой вариант
        
        # Добавляем определенных персонажей
        defined_characters = self._get_defined_characters()
        if defined_characters:
            combo.addItem("--- Персонажи ---")
            for char_name in defined_characters:
                combo.addItem(char_name)
        
        # Добавляем определенные изображения
        defined_images = self._get_defined_images()
        if defined_images:
            combo.addItem("--- Изображения ---")
            for image_name in sorted(defined_images.keys()):
                combo.addItem(image_name)
        
        value = self.current_block.params.get(key, default) if self.current_block else default
        current_text = str(value) if value else ""
        
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(current_text)
        
        combo.setToolTip(tooltip)
        combo.setStyleSheet(self._get_combo_style())
        
        self._param_widgets[key] = combo
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, combo)
    
    def _add_audio_file_field(self, key: str, label: str, default: str = "") -> None:
        """Add a combo field for selecting an audio file with file browse button"""
        label_widget = QLabel(label, self)
        tooltip = get_parameter_tooltip(key)
        label_widget.setToolTip(tooltip)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, label_widget)
        
        # Контейнер для комбобокса и кнопки
        audio_container = QHBoxLayout()
        audio_container.setSpacing(4)
        
        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItem("")  # Пустой вариант
        
        # Добавляем определенные аудио файлы
        defined_audio = self._get_defined_audio_files()
        if defined_audio:
            for audio_file in defined_audio:
                combo.addItem(audio_file)
        
        value = self.current_block.params.get(key, default) if self.current_block else default
        current_text = str(value) if value else ""
        
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(current_text)
        
        combo.setToolTip(tooltip)
        combo.setStyleSheet(self._get_combo_style())
        
        self._param_widgets[key] = combo
        audio_container.addWidget(combo, 1)
        
        # Кнопка выбора файла
        browse_btn = QPushButton("📁", self)
        browse_btn.setToolTip("Выбрать файл")
        browse_btn.setMaximumWidth(40)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                font-size: 12px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #5BA0F2;
            }
            QPushButton:pressed {
                background-color: #3A80D2;
            }
        """)
        
        def on_browse_clicked():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"Выбрать аудио файл для {label}",
                "",
                "Аудио файлы (*.ogg *.mp3 *.wav *.opus);;Все файлы (*.*)"
            )
            if file_path:
                combo.setCurrentText(file_path)
        
        browse_btn.clicked.connect(on_browse_clicked)
        audio_container.addWidget(browse_btn)
        
        audio_widget = QWidget(self)
        audio_widget.setLayout(audio_container)
        self.properties_layout.insertWidget(self.properties_layout.count() - 1, audio_widget)
    
    def _notify_scene_about_new_block(self, block: Block) -> None:
        """Уведомить сцену о новом блоке для отображения"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'node_view'):
                node_view = parent.node_view
                if hasattr(node_view, 'node_scene'):
                    scene = node_view.node_scene
                    if hasattr(scene, '_create_node_item_for_block'):
                        scene._create_node_item_for_block(block)
                        break
            parent = parent.parent()