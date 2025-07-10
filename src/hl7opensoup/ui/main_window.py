"""
Main window for HL7 OpenSoup application.

This module implements the main application window that replicates the HL7 Soup
interface layout with multiple panels for message editing, interpretation,
message list, and segment grid.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QTabWidget, QTextEdit,
    QListWidget, QTableWidget, QLabel, QFrame, QLineEdit,
    QComboBox, QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QHeaderView, QTableWidgetItem, QListWidgetItem, QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QTextCursor, QColor, QTextCharFormat

from hl7opensoup.config.app_config import AppConfig
from hl7opensoup.core.hl7_parser import HL7Parser
from hl7opensoup.core.hl7_validator import HL7Validator
from hl7opensoup.models.hl7_message import HL7Message, HL7MessageCollection


class MainWindow(QMainWindow):
    """Main application window that replicates HL7 Soup interface."""
    
    # Signals
    file_opened = pyqtSignal(str)
    file_saved = pyqtSignal(str)
    message_selected = pyqtSignal(object)
    
    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None):
        """Initialize the main window.
        
        Args:
            config: Application configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Window properties
        self.setWindowTitle("HL7 OpenSoup - Advanced HL7 Viewer and Editor")
        self.setMinimumSize(1200, 800)
        
        # Initialize UI components
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbars()
        self._setup_status_bar()
        self._apply_configuration()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Set up the main user interface layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Create main splitter (vertical)
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(self.main_splitter)
        
        # Top section: Interpretation panel
        self.interpretation_panel = self._create_interpretation_panel()
        self.main_splitter.addWidget(self.interpretation_panel)
        
        # Middle section: Horizontal splitter for editor and message list
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(middle_splitter)
        
        # Message editor (center)
        self.editor_panel = self._create_editor_panel()
        middle_splitter.addWidget(self.editor_panel)
        
        # Message list (right)
        self.message_list_panel = self._create_message_list_panel()
        middle_splitter.addWidget(self.message_list_panel)
        
        # Bottom section: Segment grid panel
        self.segment_grid_panel = self._create_segment_grid_panel()
        self.main_splitter.addWidget(self.segment_grid_panel)
        
        # Set initial splitter proportions
        self.main_splitter.setSizes([200, 400, 200])  # Top, Middle, Bottom
        middle_splitter.setSizes([600, 300])  # Editor, Message List
    
    def _create_interpretation_panel(self) -> QWidget:
        """Create the interpretation panel (top).
        
        Returns:
            Widget containing the interpretation panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(150)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("Interpretation")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Interpretation text area
        self.interpretation_text = QTextEdit()
        self.interpretation_text.setReadOnly(True)
        self.interpretation_text.setPlaceholderText(
            "Select a message or segment to view interpretation..."
        )
        layout.addWidget(self.interpretation_text)
        
        return panel
    
    def _create_editor_panel(self) -> QWidget:
        """Create the message editor panel (center).
        
        Returns:
            Widget containing the editor panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("Message Editor")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Tab widget for multiple messages
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self._close_editor_tab)
        layout.addWidget(self.editor_tabs)
        
        # Add initial tab
        self._add_editor_tab("New Message")
        
        return panel
    
    def _create_message_list_panel(self) -> QWidget:
        """Create the message list panel (right).
        
        Returns:
            Widget containing the message list panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("Messages")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Message list
        self.message_list = QListWidget()
        self.message_list.itemSelectionChanged.connect(self._on_message_selected)
        layout.addWidget(self.message_list)
        
        return panel
    
    def _create_segment_grid_panel(self) -> QWidget:
        """Create the segment grid panel (bottom).
        
        Returns:
            Widget containing the segment grid panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(150)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("Segment Grid")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Segment grid table
        self.segment_grid = QTableWidget()
        self.segment_grid.setAlternatingRowColors(True)
        layout.addWidget(self.segment_grid)
        
        return panel
    
    def _setup_menus(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # File actions will be implemented in subsequent tasks
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        help_menu.addAction(about_action)
    
    def _setup_toolbars(self):
        """Set up the application toolbars."""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Toolbar actions will be implemented in subsequent tasks
    
    def _setup_status_bar(self):
        """Set up the application status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def _apply_configuration(self):
        """Apply configuration settings to the UI."""
        # Apply font settings
        font_family = self.config.get('ui.font_family', 'Consolas')
        font_size = self.config.get('ui.font_size', 10)
        
        font = QFont(font_family, font_size)
        
        # Apply to editor tabs (will be implemented when editor is created)
        
        # Restore window geometry if available
        geometry = self.config.get('ui.window_geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.config.get('ui.window_state')
        if state:
            self.restoreState(state)
    
    def _add_editor_tab(self, title: str = "Untitled") -> QTextEdit:
        """Add a new editor tab.
        
        Args:
            title: Tab title
            
        Returns:
            The text editor widget
        """
        editor = QTextEdit()
        editor.setPlaceholderText("Enter HL7 message here...")
        
        # Apply font configuration
        font_family = self.config.get('ui.font_family', 'Consolas')
        font_size = self.config.get('ui.font_size', 10)
        font = QFont(font_family, font_size)
        editor.setFont(font)
        
        tab_index = self.editor_tabs.addTab(editor, title)
        self.editor_tabs.setCurrentIndex(tab_index)
        
        return editor
    
    def _close_editor_tab(self, index: int):
        """Close an editor tab.
        
        Args:
            index: Tab index to close
        """
        if self.editor_tabs.count() > 1:
            self.editor_tabs.removeTab(index)
        else:
            # Don't close the last tab, just clear it
            editor = self.editor_tabs.widget(index)
            if editor:
                editor.clear()
    
    def _on_message_selected(self):
        """Handle message selection in the message list."""
        # This will be implemented when message management is added
        pass
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Save window geometry and state
        self.config.set('ui.window_geometry', self.saveGeometry())
        self.config.set('ui.window_state', self.saveState())
        self.config.save_config()
        
        self.logger.info("Application closing")
        event.accept()
