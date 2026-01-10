"""Centralized styling system for professional UI/UX"""

# Color Palette - Modern Dark Theme
COLORS = {
    # Backgrounds
    'bg_primary': '#1A1A1A',      # Main background
    'bg_secondary': '#252525',    # Secondary panels
    'bg_tertiary': '#2A2A2A',     # Input fields, lists
    'bg_hover': '#2F2F2F',        # Hover states
    'bg_active': '#333333',       # Active states
    'bg_selected': '#1E3A5F',     # Selected items
    
    # Text
    'text_primary': '#E8E8E8',    # Primary text
    'text_secondary': '#B0B0B0',  # Secondary text
    'text_disabled': '#606060',   # Disabled text
    'text_highlight': '#FFFFFF',  # Highlighted text
    
    # Accent Colors
    'accent_primary': '#4A9EFF',   # Primary accent (blue)
    'accent_primary_hover': '#5BAEFF',
    'accent_primary_pressed': '#3A8EEF',
    'accent_success': '#4CAF50',  # Success green
    'accent_warning': '#FF9800',  # Warning orange
    'accent_error': '#F44336',    # Error red
    
    # Borders
    'border_primary': '#3A3A3A',
    'border_secondary': '#4A4A4A',
    'border_focus': '#4A9EFF',
    'border_hover': '#5A5A5A',
    
    # Shadows
    'shadow_light': 'rgba(0, 0, 0, 0.2)',
    'shadow_medium': 'rgba(0, 0, 0, 0.4)',
    'shadow_heavy': 'rgba(0, 0, 0, 0.6)',
}

# Typography
FONTS = {
    'family_primary': "'Segoe UI', 'Roboto', 'Arial', sans-serif",
    'family_mono': "'Consolas', 'Courier New', monospace",
    'size_small': '10px',
    'size_normal': '11px',
    'size_medium': '12px',
    'size_large': '14px',
    'size_title': '16px',
    'weight_normal': '400',
    'weight_medium': '500',
    'weight_bold': '600',
}

# Spacing
SPACING = {
    'xs': '2px',
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    'xxl': '24px',
}

# Border Radius
RADIUS = {
    'sm': '4px',
    'md': '6px',
    'lg': '8px',
    'xl': '12px',
    'round': '50%',
}

# Transitions
TRANSITION = 'all 0.2s ease-in-out'


def get_main_window_style() -> str:
    """Get stylesheet for main window"""
    return f"""
        QMainWindow {{
            background-color: {COLORS['bg_primary']};
            color: {COLORS['text_primary']};
        }}
        
        QWidget {{
            background-color: {COLORS['bg_primary']};
            color: {COLORS['text_primary']};
            font-family: {FONTS['family_primary']};
            font-size: {FONTS['size_normal']};
        }}
        
        QPushButton {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['md']} {SPACING['xl']};
            color: {COLORS['text_primary']};
            font-weight: {FONTS['weight_medium']};
            font-size: {FONTS['size_normal']};
            min-height: 28px;
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['bg_hover']};
            border-color: {COLORS['border_hover']};
            transform: translateY(-1px);
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS['bg_active']};
            border-color: {COLORS['border_secondary']};
            transform: translateY(0px);
        }}
        
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            border-color: {COLORS['border_primary']};
            color: {COLORS['text_disabled']};
        }}
        
        QPushButton#primaryButton {{
            background-color: {COLORS['accent_primary']};
            border-color: {COLORS['accent_primary']};
            color: {COLORS['text_highlight']};
        }}
        
        QPushButton#primaryButton:hover {{
            background-color: {COLORS['accent_primary_hover']};
            border-color: {COLORS['accent_primary_hover']};
        }}
        
        QPushButton#primaryButton:pressed {{
            background-color: {COLORS['accent_primary_pressed']};
            border-color: {COLORS['accent_primary_pressed']};
        }}
        
        QLabel {{
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
        }}
        
        QSplitter::handle {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border_primary']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 4px;
        }}
        
        QSplitter::handle:vertical {{
            height: 4px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {COLORS['bg_hover']};
        }}
        
        QToolBar {{
            background-color: {COLORS['bg_secondary']};
            border: none;
            border-bottom: 1px solid {COLORS['border_primary']};
            spacing: {SPACING['sm']};
            padding: {SPACING['sm']};
        }}
        
        QToolBar QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {RADIUS['sm']};
            padding: {SPACING['sm']};
            margin: {SPACING['xs']};
        }}
        
        QToolBar QToolButton:hover {{
            background-color: {COLORS['bg_hover']};
            border-color: {COLORS['border_primary']};
        }}
    """


def get_dialog_style() -> str:
    """Get stylesheet for dialogs"""
    return f"""
        QDialog {{
            background-color: {COLORS['bg_primary']};
            color: {COLORS['text_primary']};
        }}
        
        QLineEdit {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            padding: {SPACING['md']};
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            selection-background-color: {COLORS['accent_primary']};
            selection-color: {COLORS['text_highlight']};
        }}
        
        QLineEdit:focus {{
            border-color: {COLORS['border_focus']};
            background-color: {COLORS['bg_hover']};
        }}
        
        QTextEdit {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            padding: {SPACING['md']};
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            font-family: {FONTS['family_mono']};
            selection-background-color: {COLORS['accent_primary']};
            selection-color: {COLORS['text_highlight']};
        }}
        
        QTextEdit:focus {{
            border-color: {COLORS['border_focus']};
            background-color: {COLORS['bg_hover']};
        }}
        
        QComboBox {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            padding: {SPACING['md']};
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            min-height: 28px;
        }}
        
        QComboBox:hover {{
            border-color: {COLORS['border_hover']};
        }}
        
        QComboBox:focus {{
            border-color: {COLORS['border_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {COLORS['text_primary']};
            width: 0;
            height: 0;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            selection-background-color: {COLORS['accent_primary']};
            selection-color: {COLORS['text_highlight']};
            padding: {SPACING['xs']};
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            padding: {SPACING['md']};
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            min-height: 28px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {COLORS['border_focus']};
        }}
        
        QCheckBox {{
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            spacing: {SPACING['md']};
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            background-color: {COLORS['bg_tertiary']};
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {COLORS['border_hover']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {COLORS['accent_primary']};
            border-color: {COLORS['accent_primary']};
        }}
        
        QGroupBox {{
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['md']};
            margin-top: {SPACING['xl']};
            padding-top: {SPACING['lg']};
            font-weight: {FONTS['weight_medium']};
            font-size: {FONTS['size_medium']};
            color: {COLORS['text_primary']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {SPACING['lg']};
            padding: 0 {SPACING['md']};
            color: {COLORS['text_primary']};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {COLORS['border_primary']};
            background-color: {COLORS['bg_secondary']};
            border-radius: {RADIUS['sm']};
        }}
        
        QTabBar::tab {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_secondary']};
            padding: {SPACING['md']} {SPACING['xl']};
            margin-right: {SPACING['xs']};
            border-top-left-radius: {RADIUS['sm']};
            border-top-right-radius: {RADIUS['sm']};
            border-bottom: 2px solid transparent;
        }}
        
        QTabBar::tab:selected {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border-bottom: 2px solid {COLORS['accent_primary']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_primary']};
        }}
    """


def get_list_widget_style() -> str:
    """Get stylesheet for list widgets"""
    return f"""
        QListWidget {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            outline: none;
        }}
        
        QListWidget::item {{
            padding: {SPACING['md']};
            border-radius: {RADIUS['sm']};
            margin: {SPACING['xs']};
        }}
        
        QListWidget::item:selected {{
            background-color: {COLORS['accent_primary']};
            color: {COLORS['text_highlight']};
        }}
        
        QListWidget::item:hover {{
            background-color: {COLORS['bg_hover']};
        }}
        
        QListWidget::item:selected:hover {{
            background-color: {COLORS['accent_primary_hover']};
        }}
        
        QScrollBar:vertical {{
            background-color: {COLORS['bg_secondary']};
            width: 12px;
            border: none;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {COLORS['bg_hover']};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['bg_active']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {COLORS['bg_secondary']};
            height: 12px;
            border: none;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {COLORS['bg_hover']};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {COLORS['bg_active']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """


def get_panel_style() -> str:
    """Get stylesheet for side panels"""
    return f"""
        QWidget {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
        }}
        
        QLabel {{
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_normal']};
            padding: {SPACING['sm']};
        }}
    """


def get_code_editor_style() -> str:
    """Get stylesheet for code editor/preview"""
    return f"""
        QTextEdit {{
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['sm']};
            padding: {SPACING['lg']};
            color: {COLORS['text_primary']};
            font-family: {FONTS['family_mono']};
            font-size: {FONTS['size_small']};
            line-height: 1.5;
            selection-background-color: {COLORS['accent_primary']};
            selection-color: {COLORS['text_highlight']};
        }}
        
        QTextEdit:focus {{
            border-color: {COLORS['border_focus']};
        }}
    """
