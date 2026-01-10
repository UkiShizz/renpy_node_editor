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
from renpy_node_editor.runner.renpy_env import default_sdk_root, RenpyEnv


class SettingsDialog(QDialog):
    """Диалог настроек редактора"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setWindowTitle("Настройки редактора")
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
        
        # Вкладка "Ren'Py SDK"
        renpy_tab = self._create_renpy_tab()
        tabs.addTab(renpy_tab, "Ren'Py SDK")
        
        # Вкладка "Отображение"
        display_tab = self._create_display_tab()
        tabs.addTab(display_tab, "Отображение")
        
        # Вкладка "Экспорт"
        export_tab = self._create_export_tab()
        tabs.addTab(export_tab, "Экспорт")
        
        # Вкладка "Генерация кода"
        generation_tab = self._create_generation_tab()
        tabs.addTab(generation_tab, "Генерация")
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_cancel = QPushButton("Отмена", self)
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("Сохранить", self)
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._on_save)
        buttons_layout.addWidget(btn_save)
        
        layout.addLayout(buttons_layout)
    
    def _create_renpy_tab(self) -> QWidget:
        """Создать вкладку настроек Ren'Py SDK"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        group = QGroupBox("Путь к Ren'Py SDK", widget)
        group_layout = QFormLayout(group)
        group_layout.setSpacing(10)
        
        # Путь к SDK
        path_layout = QHBoxLayout()
        self.renpy_sdk_path = QLineEdit()
        self.renpy_sdk_path.setPlaceholderText("C:\\RenPy\\renpy-8.3.7")
        path_layout.addWidget(self.renpy_sdk_path)
        
        btn_browse = QPushButton("Обзор...", group)
        btn_browse.clicked.connect(self._on_browse_renpy_sdk)
        path_layout.addWidget(btn_browse)
        
        group_layout.addRow("Путь к SDK:", path_layout)
        
        # Информация о валидности
        self.renpy_status_label = QLabel("")
        self.renpy_status_label.setWordWrap(True)
        group_layout.addRow("", self.renpy_status_label)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
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
    
    def _create_export_tab(self) -> QWidget:
        """Создать вкладку настроек экспорта"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        group = QGroupBox("Пути по умолчанию", widget)
        group_layout = QFormLayout(group)
        group_layout.setSpacing(10)
        
        # Путь по умолчанию для экспорта
        export_path_layout = QHBoxLayout()
        self.default_export_path = QLineEdit()
        self.default_export_path.setPlaceholderText("Путь к папке для экспорта проектов")
        export_path_layout.addWidget(self.default_export_path)
        
        btn_browse_export = QPushButton("Обзор...", group)
        btn_browse_export.clicked.connect(self._on_browse_export_path)
        export_path_layout.addWidget(btn_browse_export)
        
        group_layout.addRow("Путь экспорта:", export_path_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_generation_tab(self) -> QWidget:
        """Создать вкладку настроек генерации кода"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        group = QGroupBox("Генерация Ren'Py кода", widget)
        group_layout = QFormLayout(group)
        group_layout.setSpacing(10)
        
        # Комментарии
        self.add_comments = QCheckBox("Добавлять комментарии в сгенерированный код")
        group_layout.addRow("", self.add_comments)
        
        # Форматирование
        indent_layout = QHBoxLayout()
        self.indent_size = QSpinBox()
        self.indent_size.setMinimum(2)
        self.indent_size.setMaximum(8)
        self.indent_size.setSuffix(" пробелов")
        indent_layout.addWidget(self.indent_size)
        indent_layout.addStretch()
        group_layout.addRow("Размер отступа:", indent_layout)
        
        # Стиль отступов
        indent_style_layout = QHBoxLayout()
        self.indent_style = QComboBox()
        self.indent_style.addItems(["Пробелы", "Табуляция"])
        indent_style_layout.addWidget(self.indent_style)
        indent_style_layout.addStretch()
        group_layout.addRow("Стиль отступов:", indent_style_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _load_current_settings(self) -> None:
        """Загрузить текущие настройки в UI"""
        # Ren'Py SDK
        renpy_path = self.settings.get("renpy_sdk_path", str(default_sdk_root()))
        self.renpy_sdk_path.setText(renpy_path)
        self._validate_renpy_path()
        
        # Отображение
        self.show_grid.setChecked(self.settings.get("show_grid", True))
        self.grid_size.setValue(self.settings.get("grid_size", 20))
        self.show_tooltips.setChecked(self.settings.get("show_tooltips", True))
        self.auto_center_on_load.setChecked(self.settings.get("auto_center_on_load", False))
        
        # Экспорт
        default_export = self.settings.get("default_export_path", "")
        self.default_export_path.setText(default_export)
        
        # Генерация
        self.add_comments.setChecked(self.settings.get("add_comments", False))
        self.indent_size.setValue(self.settings.get("indent_size", 4))
        indent_style = self.settings.get("indent_style", "spaces")
        self.indent_style.setCurrentIndex(0 if indent_style == "spaces" else 1)
    
    def _validate_renpy_path(self) -> None:
        """Проверить валидность пути к Ren'Py SDK"""
        path_str = self.renpy_sdk_path.text().strip()
        if not path_str:
            self.renpy_status_label.setText("⚠️ Путь не указан")
            self.renpy_status_label.setStyleSheet("color: #FFA500;")
            return
        
        path = Path(path_str)
        env = RenpyEnv(sdk_root=path)
        
        if env.is_valid():
            self.renpy_status_label.setText("✅ Путь к Ren'Py SDK корректен")
            self.renpy_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.renpy_status_label.setText(
                "❌ Неверный путь к Ren'Py SDK\n"
                "Убедитесь, что в указанной папке находятся файлы renpy.py и python.exe"
            )
            self.renpy_status_label.setStyleSheet("color: #F44336;")
    
    def _on_browse_renpy_sdk(self) -> None:
        """Открыть диалог выбора папки Ren'Py SDK"""
        current_path = self.renpy_sdk_path.text().strip()
        if not current_path:
            current_path = str(default_sdk_root())
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку Ren'Py SDK",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.renpy_sdk_path.setText(folder)
            self._validate_renpy_path()
    
    def _on_browse_export_path(self) -> None:
        """Открыть диалог выбора папки для экспорта"""
        current_path = self.default_export_path.text().strip()
        if not current_path:
            current_path = str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку по умолчанию для экспорта",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.default_export_path.setText(folder)
    
    def _on_save(self) -> None:
        """Сохранить настройки"""
        # Проверяем путь к Ren'Py SDK
        renpy_path = self.renpy_sdk_path.text().strip()
        if renpy_path:
            env = RenpyEnv(sdk_root=Path(renpy_path))
            if not env.is_valid():
                reply = QMessageBox.question(
                    self,
                    "Неверный путь к Ren'Py SDK",
                    "Указанный путь к Ren'Py SDK неверен. Сохранить настройки всё равно?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        # Сохраняем настройки
        self.settings["renpy_sdk_path"] = renpy_path
        self.settings["show_grid"] = self.show_grid.isChecked()
        self.settings["grid_size"] = self.grid_size.value()
        self.settings["show_tooltips"] = self.show_tooltips.isChecked()
        self.settings["auto_center_on_load"] = self.auto_center_on_load.isChecked()
        self.settings["default_export_path"] = self.default_export_path.text().strip()
        self.settings["add_comments"] = self.add_comments.isChecked()
        self.settings["indent_size"] = self.indent_size.value()
        self.settings["indent_style"] = "spaces" if self.indent_style.currentIndex() == 0 else "tabs"
        
        save_settings(self.settings)
        
        QMessageBox.information(
            self,
            "Настройки сохранены",
            "Настройки успешно сохранены.\n\n"
            "Некоторые изменения могут потребовать перезапуска редактора."
        )
        
        self.accept()
