from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QGroupBox, QCheckBox, QSpinBox, QMessageBox, QTabWidget,
    QWidget, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from renpy_node_editor.core.settings import load_settings, save_settings
from renpy_node_editor.core.i18n import tr, get_language, set_language, reload_translations
from PySide6.QtCore import Signal


class SettingsDialog(QDialog):
    """Диалог настроек редактора"""
    
    language_changed = Signal(str)  # emits language code
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setWindowTitle(tr("ui.settings.title", "Настройки редактора"))
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        # Применяем стиль
        self._apply_style()
        
        # Загружаем текущие настройки
        self.settings = load_settings()
        
        self._build_ui()
        self._load_current_settings()
    
    def _apply_style(self) -> None:
        """Применить стиль к диалогу"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                background-color: #2F2F2F;
            }
            QPushButton {
                background-color: #3A3A3A;
                border: 2px solid #4A4A4A;
                border-radius: 6px;
                padding: 8px 16px;
                color: #E0E0E0;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
                border-color: #5A5A5A;
            }
            QPushButton:pressed {
                background-color: #2A2A2A;
            }
            QPushButton#primaryButton {
                background-color: #4A90E2;
                border: 2px solid #5BA0F2;
                color: #FFFFFF;
            }
            QPushButton#primaryButton:hover {
                background-color: #5BA0F2;
                border-color: #6BB0FF;
            }
            QGroupBox {
                border: 2px solid #3A3A3A;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 12px;
                color: #E0E0E0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 11px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3A3A3A;
                border-radius: 3px;
                background-color: #2A2A2A;
            }
            QCheckBox::indicator:checked {
                background-color: #4A90E2;
                border-color: #6BA3F0;
            }
            QSpinBox {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 11px;
            }
            QSpinBox:focus {
                border-color: #4A90E2;
            }
            QTabWidget::pane {
                border: 1px solid #3A3A3A;
                background-color: #252525;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2A2A2A;
                color: #E0E0E0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4A90E2;
                color: #FFFFFF;
            }
            QTabBar::tab:hover {
                background-color: #3A3A3A;
            }
            QComboBox {
                background-color: #2A2A2A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 11px;
            }
            QComboBox:focus {
                border-color: #4A90E2;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #E0E0E0;
            }
        """)
    
    def _build_ui(self) -> None:
        """Построить UI диалога"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Вкладки для разных категорий настроек
        tabs = QTabWidget(self)
        layout.addWidget(tabs)
        
        # Вкладка "Отображение"
        display_tab = self._create_display_tab()
        tabs.addTab(display_tab, tr("ui.settings.tab.display", "Отображение"))
        
        # Вкладка "Язык"
        language_tab = self._create_language_tab()
        tabs.addTab(language_tab, tr("ui.settings.tab.language", "Язык"))
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_cancel = QPushButton(tr("ui.settings.cancel", "Отмена"), self)
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton(tr("ui.settings.ok", "OK"), self)
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._on_save)
        buttons_layout.addWidget(btn_save)
        
        layout.addLayout(buttons_layout)
    
    def _create_display_tab(self) -> QWidget:
        """Создать вкладку настроек отображения"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Сетка
        grid_group = QGroupBox("Сетка", widget)
        grid_layout = QFormLayout(grid_group)
        grid_layout.setSpacing(10)
        
        self.show_grid = QCheckBox("Показывать сетку на рабочей области")
        grid_layout.addRow("", self.show_grid)
        
        grid_size_layout = QHBoxLayout()
        self.grid_size = QSpinBox()
        self.grid_size.setMinimum(10)
        self.grid_size.setMaximum(100)
        self.grid_size.setSuffix(" px")
        grid_size_layout.addWidget(self.grid_size)
        grid_size_layout.addStretch()
        grid_layout.addRow("Размер сетки:", grid_size_layout)
        
        layout.addWidget(grid_group)
        
        # Дополнительные настройки
        other_group = QGroupBox("Дополнительно", widget)
        other_layout = QFormLayout(other_group)
        other_layout.setSpacing(10)
        
        self.show_tooltips = QCheckBox("Показывать подсказки при наведении")
        other_layout.addRow("", self.show_tooltips)
        
        self.auto_center_on_load = QCheckBox("Автоматически центрировать при загрузке проекта")
        other_layout.addRow("", self.auto_center_on_load)
        
        layout.addWidget(other_group)
        layout.addStretch()
        
        return widget
    
    def _create_language_tab(self) -> QWidget:
        """Создать вкладку настроек языка"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        group = QGroupBox("Язык интерфейса", widget)
        group_layout = QFormLayout(group)
        group_layout.setSpacing(10)
        
        # Выбор языка
        language_layout = QHBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        group_layout.addRow("Язык:", language_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _load_current_settings(self) -> None:
        """Загрузить текущие настройки в UI"""
        # Отображение
        self.show_grid.setChecked(self.settings.get("show_grid", True))
        self.grid_size.setValue(self.settings.get("grid_size", 20))
        self.show_tooltips.setChecked(self.settings.get("show_tooltips", True))
        self.auto_center_on_load.setChecked(self.settings.get("auto_center_on_load", False))
        
        # Язык
        current_lang = self.settings.get("language", "en")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
    
    def _on_save(self) -> None:
        """Сохранить настройки"""
        # Сохраняем настройки
        self.settings["show_grid"] = self.show_grid.isChecked()
        self.settings["grid_size"] = self.grid_size.value()
        self.settings["show_tooltips"] = self.show_tooltips.isChecked()
        self.settings["auto_center_on_load"] = self.auto_center_on_load.isChecked()
        
        # Сохраняем язык
        selected_lang = self.language_combo.currentData()
        if selected_lang:
            old_lang = self.settings.get("language", "en")
            self.settings["language"] = selected_lang
            set_language(selected_lang)
            reload_translations()
            # Эмитим сигнал, если язык изменился
            if selected_lang != old_lang:
                self.language_changed.emit(selected_lang)
        
        save_settings(self.settings)
        
        QMessageBox.information(
            self,
            "Настройки сохранены",
            "Настройки успешно сохранены.\n\n"
            "Некоторые изменения могут потребовать перезапуска редактора."
        )
        
        self.accept()
