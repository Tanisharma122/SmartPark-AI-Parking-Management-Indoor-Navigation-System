
# HikCentral-like Dark Theme Colors
COLOR_BG_MAIN = "#1a1a1a"   # Deep dark grey background
COLOR_BG_PANEL = "#252525"  # Slightly lighter panel background
COLOR_BORDER = "#3a3a3a"    # Borders
COLOR_ACCENT = "#e63946"    # Red accent (Hikvision red)
COLOR_TEXT_MAIN = "#ffffff" 
COLOR_TEXT_DIM = "#a0a0a0"
COLOR_SLOT_FREE = "#2ecc71" # Green
COLOR_SLOT_OCC = "#e74c3c"  # Red
COLOR_SLOT_RESERVED = "#f1c40f" # Yellow
COLOR_VIOLATION = "#e67e22" # Orange

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG_MAIN};
}}

QWidget {{
    color: {COLOR_TEXT_MAIN};
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}}

/* Panels */
.QFrame#SidePanel {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
}}

/* Headers */
QLabel#PanelHeader {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_TEXT_MAIN};
    padding: 8px;
    background-color: {COLOR_BORDER};
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

/* Stat Cards */
QFrame#StatCard {{
    background-color: {COLOR_BG_MAIN};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
}}

/* List Items */
QListWidget {{
    background-color: {COLOR_BG_PANEL};
    border: none;
}}
QListWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QListWidget::item:selected {{
    background-color: {COLOR_ACCENT};
}}

/* Buttons */
QPushButton {{
    background-color: {COLOR_BORDER};
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    color: {COLOR_TEXT_MAIN};
}}
QPushButton:hover {{
    background-color: #4a4a4a;
}}
QPushButton#ActionButton {{
    background-color: {COLOR_ACCENT};
    font-weight: bold;
}}
QPushButton#ActionButton:hover {{
    background-color: #d62c1a;
}}

/* Progress Bar */
QProgressBar {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 2px;
    text-align: center;
    background-color: {COLOR_BG_MAIN};
}}
QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
}}
"""
