"""
HL7 Soup Style Sheet for HL7 OpenSoup.

This module provides styling to replicate the look and feel of the original
HL7 Soup desktop application.
"""

# Main application stylesheet that replicates HL7 Soup appearance
HL7_SOUP_STYLESHEET = """
/* Main Application Window */
QMainWindow {
    background-color: #f0f0f0;
    color: #000000;
}

/* Menu Bar */
QMenuBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #c0c0c0;
    padding: 2px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
    margin: 1px;
}

QMenuBar::item:selected {
    background-color: #d0d0d0;
    border: 1px solid #a0a0a0;
}

QMenuBar::item:pressed {
    background-color: #c0c0c0;
}

/* Tool Bar */
QToolBar {
    background-color: #e8e8e8;
    border: 1px solid #c0c0c0;
    spacing: 2px;
    padding: 2px;
}

QToolBar::separator {
    background-color: #c0c0c0;
    width: 1px;
    margin: 2px;
}

/* Status Bar */
QStatusBar {
    background-color: #e8e8e8;
    border-top: 1px solid #c0c0c0;
    padding: 2px;
}

/* Splitters */
QSplitter::handle {
    background-color: #d0d0d0;
    border: 1px solid #a0a0a0;
}

QSplitter::handle:horizontal {
    width: 6px;
}

QSplitter::handle:vertical {
    height: 6px;
}

QSplitter::handle:pressed {
    background-color: #b0b0b0;
}

/* Panels and Frames */
QFrame[frameShape="4"] {  /* StyledPanel */
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    padding: 4px;
}

/* Panel Titles */
QLabel[panelTitle="true"] {
    background-color: #e0e0e0;
    border: 1px solid #a0a0a0;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 11px;
    color: #000080;
}

/* Tab Widget */
QTabWidget::pane {
    border: 2px inset #d0d0d0;
    background-color: #ffffff;
}

QTabWidget::tab-bar {
    left: 5px;
}

QTabBar::tab {
    background-color: #e8e8e8;
    border: 1px solid #a0a0a0;
    border-bottom: none;
    padding: 4px 12px;
    margin-right: 2px;
    font-size: 10px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: 1px solid #ffffff;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

QTabBar::tab:hover {
    background-color: #f0f0f0;
}

/* Text Editors */
QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    selection-background-color: #316AC5;
    selection-color: #ffffff;
    font-family: "Courier New", "Consolas", monospace;
    font-size: 10px;
    line-height: 1.2;
}

QPlainTextEdit:focus, QTextEdit:focus {
    border: 2px inset #4080ff;
}

/* List Widgets */
QListWidget {
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    alternate-background-color: #f8f8f8;
    selection-background-color: #316AC5;
    selection-color: #ffffff;
    font-size: 10px;
}

QListWidget::item {
    padding: 2px 4px;
    border-bottom: 1px solid #e0e0e0;
}

QListWidget::item:selected {
    background-color: #316AC5;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #e0e8ff;
}

/* Table Widgets */
QTableWidget {
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    gridline-color: #d0d0d0;
    selection-background-color: #316AC5;
    selection-color: #ffffff;
    font-size: 10px;
}

QTableWidget::item {
    padding: 2px 4px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #316AC5;
    color: #ffffff;
}

QTableWidget::item:hover {
    background-color: #e0e8ff;
}

QHeaderView::section {
    background-color: #e8e8e8;
    border: 1px solid #a0a0a0;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 10px;
}

QHeaderView::section:pressed {
    background-color: #d0d0d0;
}

/* Buttons */
QPushButton {
    background-color: #e8e8e8;
    border: 2px outset #d0d0d0;
    padding: 4px 12px;
    font-size: 10px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: #f0f0f0;
}

QPushButton:pressed {
    border: 2px inset #d0d0d0;
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f0f0f0;
    color: #808080;
    border: 2px outset #e0e0e0;
}

/* Combo Boxes */
QComboBox {
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    padding: 2px 4px;
    font-size: 10px;
    min-width: 80px;
}

QComboBox:hover {
    border: 2px inset #4080ff;
}

QComboBox::drop-down {
    border: none;
    width: 16px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #606060;
    margin-right: 4px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #a0a0a0;
    selection-background-color: #316AC5;
    selection-color: #ffffff;
}

/* Line Edits */
QLineEdit {
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    padding: 2px 4px;
    font-size: 10px;
}

QLineEdit:focus {
    border: 2px inset #4080ff;
}

QLineEdit:disabled {
    background-color: #f0f0f0;
    color: #808080;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 16px;
    border: 1px solid #a0a0a0;
}

QScrollBar::handle:vertical {
    background-color: #d0d0d0;
    border: 1px solid #a0a0a0;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #c0c0c0;
}

QScrollBar::handle:vertical:pressed {
    background-color: #b0b0b0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background-color: #e0e0e0;
    border: 1px solid #a0a0a0;
    height: 16px;
}

QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {
    background-color: #d0d0d0;
}

QScrollBar::add-line:vertical:pressed, QScrollBar::sub-line:vertical:pressed {
    background-color: #c0c0c0;
}

QScrollBar:horizontal {
    background-color: #f0f0f0;
    height: 16px;
    border: 1px solid #a0a0a0;
}

QScrollBar::handle:horizontal {
    background-color: #d0d0d0;
    border: 1px solid #a0a0a0;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #c0c0c0;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #b0b0b0;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background-color: #e0e0e0;
    border: 1px solid #a0a0a0;
    width: 16px;
}

/* Progress Bar */
QProgressBar {
    background-color: #ffffff;
    border: 2px inset #d0d0d0;
    text-align: center;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #316AC5;
}

/* Tool Tips */
QToolTip {
    background-color: #ffffcc;
    border: 1px solid #808080;
    padding: 4px;
    font-size: 10px;
    color: #000000;
}

/* Context Menus */
QMenu {
    background-color: #f0f0f0;
    border: 1px solid #808080;
    padding: 2px;
}

QMenu::item {
    background-color: transparent;
    padding: 4px 20px;
    font-size: 10px;
}

QMenu::item:selected {
    background-color: #316AC5;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #c0c0c0;
    margin: 2px 0px;
}

/* Message Boxes */
QMessageBox {
    background-color: #f0f0f0;
    font-size: 10px;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 4px 16px;
}

/* Specific HL7 Soup styling */
QLabel[messageCount="true"] {
    color: #606060;
    font-size: 9px;
    font-style: italic;
}

QListWidget[messageList="true"] {
    font-family: "Courier New", "Consolas", monospace;
}

QTableWidget[segmentGrid="true"] {
    font-family: "Courier New", "Consolas", monospace;
}

/* Validation status colors */
QListWidget::item[validationStatus="valid"] {
    background-color: #e8f5e8;
}

QListWidget::item[validationStatus="warning"] {
    background-color: #fff8e1;
}

QListWidget::item[validationStatus="error"] {
    background-color: #ffeaea;
}

/* HL7 Syntax highlighting colors in editor */
QPlainTextEdit[hl7Editor="true"] {
    font-family: "Courier New", "Consolas", monospace;
    font-size: 10px;
    line-height: 1.1;
}
"""

# Color scheme constants matching HL7 Soup
class HL7SoupColors:
    """Color constants matching HL7 Soup color scheme."""
    
    # Background colors
    WINDOW_BACKGROUND = "#f0f0f0"
    PANEL_BACKGROUND = "#ffffff"
    TOOLBAR_BACKGROUND = "#e8e8e8"
    
    # Border colors
    BORDER_NORMAL = "#a0a0a0"
    BORDER_INSET = "#d0d0d0"
    BORDER_FOCUS = "#4080ff"
    
    # Text colors
    TEXT_NORMAL = "#000000"
    TEXT_DISABLED = "#808080"
    TEXT_TITLE = "#000080"
    
    # Selection colors
    SELECTION_BACKGROUND = "#316AC5"
    SELECTION_TEXT = "#ffffff"
    
    # Validation status colors
    VALID_BACKGROUND = "#e8f5e8"
    WARNING_BACKGROUND = "#fff8e1"
    ERROR_BACKGROUND = "#ffeaea"
    
    # HL7 Syntax highlighting colors
    SEGMENT_COLOR = "#0000ff"      # Blue for segment names
    FIELD_SEP_COLOR = "#ff0000"    # Red for field separators
    COMPONENT_SEP_COLOR = "#ff8000" # Orange for component separators
    REPETITION_SEP_COLOR = "#800080" # Purple for repetition separators
    SUBCOMP_SEP_COLOR = "#008000"  # Green for subcomponent separators
    ESCAPE_COLOR = "#ff00ff"       # Magenta for escape characters
    ENCODING_CHARS_COLOR = "#808080" # Gray for MSH encoding characters


def apply_hl7_soup_style(app):
    """Apply HL7 Soup styling to the application.
    
    Args:
        app: QApplication instance
    """
    app.setStyleSheet(HL7_SOUP_STYLESHEET)


def get_panel_title_style():
    """Get the style for panel titles.
    
    Returns:
        Style string for panel titles
    """
    return """
    QLabel {
        background-color: #e0e0e0;
        border: 1px solid #a0a0a0;
        padding: 4px 8px;
        font-weight: bold;
        font-size: 11px;
        color: #000080;
        margin-bottom: 2px;
    }
    """


def get_message_list_style():
    """Get the style for message list with validation colors.
    
    Returns:
        Style string for message list
    """
    return """
    QListWidget {
        background-color: #ffffff;
        border: 2px inset #d0d0d0;
        font-family: "Courier New", "Consolas", monospace;
        font-size: 10px;
    }
    """


def get_segment_grid_style():
    """Get the style for segment grid.
    
    Returns:
        Style string for segment grid
    """
    return """
    QTableWidget {
        background-color: #ffffff;
        border: 2px inset #d0d0d0;
        gridline-color: #d0d0d0;
        font-family: "Courier New", "Consolas", monospace;
        font-size: 10px;
    }
    
    QHeaderView::section {
        background-color: #e8e8e8;
        border: 1px solid #a0a0a0;
        padding: 4px 8px;
        font-weight: bold;
        font-size: 10px;
    }
    """
