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
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer, QPoint
from PyQt6.QtGui import QAction, QIcon, QFont, QTextCursor, QColor, QTextCharFormat

from hl7opensoup.config.app_config import AppConfig
from hl7opensoup.core.hl7_parser import HL7Parser
from hl7opensoup.core.hl7_validator import HL7Validator
from hl7opensoup.core.hl7_interpreter import HL7Interpreter
from hl7opensoup.models.hl7_message import HL7Message, HL7MessageCollection
from hl7opensoup.ui.hl7_editor import HL7TextEditor
from hl7opensoup.ui.hl7_soup_style import (
    HL7SoupColors, get_panel_title_style, get_message_list_style, get_segment_grid_style
)
from hl7opensoup.utils.file_utils import HL7FileManager, HL7FileValidator
from hl7opensoup.ui.search_dialog import AdvancedSearchDialog


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

        # Initialize core components
        self.hl7_parser = HL7Parser()
        self.hl7_validator = HL7Validator()
        self.hl7_interpreter = HL7Interpreter()
        self.file_manager = HL7FileManager()
        self.current_collection: Optional[HL7MessageCollection] = None
        self.current_message: Optional[HL7Message] = None
        self.current_segment_index: int = -1

        # Search dialog
        self.search_dialog: Optional[AdvancedSearchDialog] = None

        # Window properties
        self.setWindowTitle("HL7 OpenSoup - Advanced HL7 Viewer and Editor")
        self.setMinimumSize(1200, 800)

        # Initialize UI components
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbars()
        self._setup_status_bar()
        self._apply_configuration()
        self._connect_signals()

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
        panel.setStyleSheet(f"background-color: {HL7SoupColors.PANEL_BACKGROUND};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Title bar
        title_label = QLabel("Interpretation")
        title_label.setStyleSheet(get_panel_title_style())
        title_label.setProperty("panelTitle", True)
        layout.addWidget(title_label)

        # Interpretation text area
        self.interpretation_text = QTextEdit()
        self.interpretation_text.setReadOnly(True)
        self.interpretation_text.setPlaceholderText(
            "Select a message or segment to view interpretation..."
        )
        self.interpretation_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10px;
                padding: 4px;
            }}
        """)
        layout.addWidget(self.interpretation_text)

        return panel
    
    def _create_editor_panel(self) -> QWidget:
        """Create the message editor panel (center).

        Returns:
            Widget containing the editor panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet(f"background-color: {HL7SoupColors.PANEL_BACKGROUND};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Title bar
        title_label = QLabel("Message Editor")
        title_label.setStyleSheet(get_panel_title_style())
        title_label.setProperty("panelTitle", True)
        layout.addWidget(title_label)

        # Tab widget for multiple messages
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self._close_editor_tab)
        self.editor_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
            }}
            QTabBar::tab {{
                background-color: {HL7SoupColors.TOOLBAR_BACKGROUND};
                border: 1px solid {HL7SoupColors.BORDER_NORMAL};
                border-bottom: none;
                padding: 4px 12px;
                margin-right: 2px;
                font-size: 10px;
            }}
            QTabBar::tab:selected {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border-bottom: 1px solid {HL7SoupColors.PANEL_BACKGROUND};
            }}
        """)
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
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(450)
        panel.setStyleSheet(f"background-color: {HL7SoupColors.PANEL_BACKGROUND};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Title bar
        title_label = QLabel("Messages")
        title_label.setStyleSheet(get_panel_title_style())
        title_label.setProperty("panelTitle", True)
        layout.addWidget(title_label)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter messages...")
        self.filter_input.textChanged.connect(self._filter_messages)
        self.filter_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                padding: 2px 4px;
                font-size: 10px;
            }}
            QLineEdit:focus {{
                border: 2px inset {HL7SoupColors.BORDER_FOCUS};
            }}
        """)
        filter_layout.addWidget(self.filter_input)

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems([
            "All", "Content", "Type", "Control ID", "Segment", "Field Value",
            "Validation Status", "Message Size"
        ])
        self.filter_type_combo.currentTextChanged.connect(self._filter_messages)
        self.filter_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                padding: 2px 4px;
                font-size: 10px;
                min-width: 80px;
            }}
        """)
        filter_layout.addWidget(self.filter_type_combo)

        layout.addLayout(filter_layout)

        # Message count label
        self.message_count_label = QLabel("0 messages")
        self.message_count_label.setStyleSheet(f"""
            color: {HL7SoupColors.TEXT_DISABLED};
            font-size: 9px;
            font-style: italic;
            padding: 2px;
        """)
        self.message_count_label.setProperty("messageCount", True)
        layout.addWidget(self.message_count_label)

        # Message list
        self.message_list = QListWidget()
        self.message_list.itemSelectionChanged.connect(self._on_message_selected)
        self.message_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.message_list.customContextMenuRequested.connect(self._show_message_context_menu)
        self.message_list.itemDoubleClicked.connect(self._on_message_double_clicked)
        self.message_list.setAlternatingRowColors(True)
        self.message_list.setStyleSheet(get_message_list_style())
        self.message_list.setProperty("messageList", True)
        layout.addWidget(self.message_list)

        # Message list controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)

        button_style = f"""
            QPushButton {{
                background-color: {HL7SoupColors.TOOLBAR_BACKGROUND};
                border: 2px outset {HL7SoupColors.BORDER_INSET};
                padding: 3px 8px;
                font-size: 10px;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background-color: #f0f0f0;
            }}
            QPushButton:pressed {{
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                background-color: {HL7SoupColors.BORDER_INSET};
            }}
            QPushButton:disabled {{
                background-color: #f0f0f0;
                color: {HL7SoupColors.TEXT_DISABLED};
                border: 2px outset #e0e0e0;
            }}
        """

        self.add_message_btn = QPushButton("Add")
        self.add_message_btn.setToolTip("Add new message")
        self.add_message_btn.clicked.connect(self._add_new_message)
        self.add_message_btn.setStyleSheet(button_style)
        controls_layout.addWidget(self.add_message_btn)

        self.copy_message_btn = QPushButton("Copy")
        self.copy_message_btn.setToolTip("Copy selected message")
        self.copy_message_btn.clicked.connect(self._copy_selected_message)
        self.copy_message_btn.setEnabled(False)
        self.copy_message_btn.setStyleSheet(button_style)
        controls_layout.addWidget(self.copy_message_btn)

        self.delete_message_btn = QPushButton("Delete")
        self.delete_message_btn.setToolTip("Delete selected message")
        self.delete_message_btn.clicked.connect(self._delete_selected_message)
        self.delete_message_btn.setEnabled(False)
        self.delete_message_btn.setStyleSheet(button_style)
        controls_layout.addWidget(self.delete_message_btn)

        layout.addLayout(controls_layout)

        return panel
    
    def _create_segment_grid_panel(self) -> QWidget:
        """Create the segment grid panel (bottom).

        Returns:
            Widget containing the segment grid panel
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(180)
        panel.setStyleSheet(f"background-color: {HL7SoupColors.PANEL_BACKGROUND};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Title bar with controls
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title_label = QLabel("Segment Grid")
        title_label.setStyleSheet(get_panel_title_style())
        title_label.setProperty("panelTitle", True)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Segment selector
        segment_label = QLabel("Segment:")
        segment_label.setStyleSheet(f"""
            QLabel {{
                color: {HL7SoupColors.TEXT_NORMAL};
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }}
        """)
        header_layout.addWidget(segment_label)

        self.segment_selector = QComboBox()
        self.segment_selector.setMinimumWidth(120)
        self.segment_selector.currentTextChanged.connect(self._on_segment_selected)
        self.segment_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                padding: 2px 4px;
                font-size: 10px;
                font-family: "Courier New", "Consolas", monospace;
            }}
        """)
        header_layout.addWidget(self.segment_selector)

        layout.addLayout(header_layout)

        # Segment grid table
        self.segment_grid = QTableWidget()
        self.segment_grid.setAlternatingRowColors(True)
        self.segment_grid.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.segment_grid.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.segment_grid.itemChanged.connect(self._on_grid_item_changed)
        self.segment_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.segment_grid.customContextMenuRequested.connect(self._show_grid_context_menu)
        self.segment_grid.itemSelectionChanged.connect(self._on_grid_selection_changed)
        self.segment_grid.setStyleSheet(get_segment_grid_style())
        self.segment_grid.setProperty("segmentGrid", True)

        # Set up columns
        self.segment_grid.setColumnCount(4)
        self.segment_grid.setHorizontalHeaderLabels(["Field", "Name", "Value", "Description"])

        # Configure column widths
        header = self.segment_grid.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # Style the header
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {HL7SoupColors.TOOLBAR_BACKGROUND};
                border: 1px solid {HL7SoupColors.BORDER_NORMAL};
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
                color: {HL7SoupColors.TEXT_TITLE};
            }}
            QHeaderView::section:pressed {{
                background-color: {HL7SoupColors.BORDER_INSET};
            }}
        """)

        layout.addWidget(self.segment_grid)

        return panel
    
    def _setup_menus(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        self.new_action = QAction("&New", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.setStatusTip("Create a new HL7 message")
        self.new_action.triggered.connect(self._new_message)
        file_menu.addAction(self.new_action)

        self.open_action = QAction("&Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Open HL7 file")
        self.open_action.triggered.connect(self._open_file)
        file_menu.addAction(self.open_action)

        file_menu.addSeparator()

        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Save current message")
        self.save_action.triggered.connect(self._save_file)
        self.save_action.setEnabled(False)
        file_menu.addAction(self.save_action)

        self.save_as_action = QAction("Save &As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.setStatusTip("Save message as new file")
        self.save_as_action.triggered.connect(self._save_file_as)
        self.save_as_action.setEnabled(False)
        file_menu.addAction(self.save_as_action)

        file_menu.addSeparator()

        # Recent files submenu
        self.recent_menu = file_menu.addMenu("Recent Files")
        self._update_recent_files_menu()

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        self.copy_action = QAction("&Copy", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.setStatusTip("Copy selected text")
        self.copy_action.triggered.connect(self._copy_text)
        edit_menu.addAction(self.copy_action)

        self.paste_action = QAction("&Paste", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.setStatusTip("Paste text")
        self.paste_action.triggered.connect(self._paste_text)
        edit_menu.addAction(self.paste_action)

        edit_menu.addSeparator()

        self.find_action = QAction("&Find", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.setStatusTip("Find text in message")
        self.find_action.triggered.connect(self._show_find_dialog)
        edit_menu.addAction(self.find_action)

        self.advanced_search_action = QAction("&Advanced Search...", self)
        self.advanced_search_action.setShortcut("Ctrl+Shift+F")
        self.advanced_search_action.setStatusTip("Advanced search with regex support")
        self.advanced_search_action.triggered.connect(self._show_advanced_search)
        edit_menu.addAction(self.advanced_search_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.refresh_action = QAction("&Refresh", self)
        self.refresh_action.setShortcut("F5")
        self.refresh_action.setStatusTip("Refresh current view")
        self.refresh_action.triggered.connect(self._refresh_view)
        view_menu.addAction(self.refresh_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        self.validate_action = QAction("&Validate Message", self)
        self.validate_action.setShortcut("Ctrl+T")
        self.validate_action.setStatusTip("Validate current message")
        self.validate_action.triggered.connect(self._validate_message)
        self.validate_action.setEnabled(False)
        tools_menu.addAction(self.validate_action)

        tools_menu.addSeparator()

        self.export_action = QAction("&Export...", self)
        self.export_action.setStatusTip("Export message to different format")
        self.export_action.triggered.connect(self._export_message)
        self.export_action.setEnabled(False)
        tools_menu.addAction(self.export_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.setStatusTip("About HL7 OpenSoup")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbars(self):
        """Set up the application toolbars."""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setObjectName("MainToolBar")  # Set object name for state saving
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
    
    def _add_editor_tab(self, title: str = "Untitled") -> HL7TextEditor:
        """Add a new editor tab.

        Args:
            title: Tab title

        Returns:
            The HL7 text editor widget
        """
        editor = HL7TextEditor()
        editor.setPlaceholderText("Enter HL7 message here...")

        # Connect editor signals
        editor.segment_clicked.connect(self._on_segment_clicked)
        editor.field_clicked.connect(self._on_field_clicked)
        editor.content_changed.connect(self._on_editor_content_changed)

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
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Editor tab changes
        self.editor_tabs.currentChanged.connect(self._on_editor_tab_changed)

        # Message list selection
        self.message_list.itemSelectionChanged.connect(self._on_message_selected)

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        if self.config.get('application.auto_save', True):
            interval = self.config.get('application.auto_save_interval', 300) * 1000
            self.auto_save_timer.start(interval)

    def _on_editor_tab_changed(self, index: int):
        """Handle editor tab change."""
        if index >= 0:
            editor = self.editor_tabs.widget(index)
            if editor and hasattr(editor, 'hl7_message'):
                self.current_message = editor.hl7_message
                self._update_interpretation_panel()
                self._update_segment_grid()

    def _on_message_selected(self):
        """Handle message selection in the message list."""
        current_item = self.message_list.currentItem()
        has_selection = current_item is not None

        # Enable/disable message controls
        self.copy_message_btn.setEnabled(has_selection)
        self.delete_message_btn.setEnabled(has_selection)

        if current_item and self.current_collection:
            message_index = self.message_list.row(current_item)
            if 0 <= message_index < len(self.current_collection):
                self.current_message = self.current_collection[message_index]
                self._load_message_in_editor(self.current_message)
                self._update_interpretation_panel()
                self._update_segment_grid()

    def _on_message_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on message list item."""
        if item and self.current_collection:
            message_index = self.message_list.row(item)
            if 0 <= message_index < len(self.current_collection):
                message = self.current_collection[message_index]
                # Open in new tab
                editor = self._add_editor_tab(f"Message {message.get_control_id()}")
                editor.set_hl7_message(message)

    def _show_message_context_menu(self, position: QPoint):
        """Show context menu for message list."""
        item = self.message_list.itemAt(position)
        if not item:
            return

        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        open_action = menu.addAction("Open in New Tab")
        open_action.triggered.connect(lambda: self._on_message_double_clicked(item))

        copy_action = menu.addAction("Copy Message")
        copy_action.triggered.connect(self._copy_selected_message)

        menu.addSeparator()

        validate_action = menu.addAction("Validate Message")
        validate_action.triggered.connect(self._validate_selected_message)

        export_action = menu.addAction("Export Message...")
        export_action.triggered.connect(self._export_selected_message)

        menu.addSeparator()

        delete_action = menu.addAction("Delete Message")
        delete_action.triggered.connect(self._delete_selected_message)

        menu.exec(self.message_list.mapToGlobal(position))

    def _add_new_message(self):
        """Add a new message to the collection."""
        if not self.current_collection:
            # Create new collection if none exists
            self.current_collection = HL7MessageCollection()

        # Create a basic MSH segment
        new_message_content = "MSH|^~\\&||||||||||||"
        try:
            new_message = self.hl7_parser.parse_message(new_message_content)
            if new_message:
                self.current_collection.add_message(new_message)
                self._populate_message_list(self.current_collection.messages)

                # Select the new message
                self.message_list.setCurrentRow(len(self.current_collection.messages) - 1)

                # Mark as modified
                self._mark_as_modified()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create new message: {e}")

    def _copy_selected_message(self):
        """Copy the selected message."""
        current_item = self.message_list.currentItem()
        if current_item and self.current_collection:
            message_index = self.message_list.row(current_item)
            if 0 <= message_index < len(self.current_collection):
                original_message = self.current_collection[message_index]

                # Create a copy
                try:
                    copied_message = self.hl7_parser.parse_message(str(original_message))
                    if copied_message:
                        # Update control ID to make it unique
                        msh = copied_message.get_msh_segment()
                        if msh:
                            original_id = msh.get_field_value(10)
                            new_id = f"{original_id}_COPY"
                            msh.set_field(10, new_id)

                        self.current_collection.add_message(copied_message)
                        self._populate_message_list(self.current_collection.messages)

                        # Select the copied message
                        self.message_list.setCurrentRow(len(self.current_collection.messages) - 1)

                        # Mark as modified
                        self._mark_as_modified()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to copy message: {e}")

    def _delete_selected_message(self):
        """Delete the selected message."""
        current_item = self.message_list.currentItem()
        if current_item and self.current_collection:
            message_index = self.message_list.row(current_item)
            if 0 <= message_index < len(self.current_collection):
                # Confirm deletion
                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    "Are you sure you want to delete this message?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.current_collection.remove_message(message_index)
                    self._populate_message_list(self.current_collection.messages)

                    # Clear current message if it was deleted
                    if self.current_message == self.current_collection[message_index]:
                        self.current_message = None
                        self._update_interpretation_panel()
                        self._update_segment_grid()

                    # Mark as modified
                    self._mark_as_modified()

    def _validate_selected_message(self):
        """Validate the selected message."""
        current_item = self.message_list.currentItem()
        if current_item and self.current_collection:
            message_index = self.message_list.row(current_item)
            if 0 <= message_index < len(self.current_collection):
                message = self.current_collection[message_index]

                try:
                    results = self.hl7_validator.validate_message(message)

                    error_count = len([r for r in results if r.level.value == "error"])
                    warning_count = len([r for r in results if r.level.value == "warning"])

                    if error_count == 0 and warning_count == 0:
                        QMessageBox.information(self, "Validation", "Message is valid!")
                    else:
                        msg = f"Validation results:\n{error_count} errors, {warning_count} warnings"
                        QMessageBox.warning(self, "Validation", msg)

                    # Update the message list to reflect validation status
                    self._populate_message_list(self.current_collection.messages)

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Validation failed: {e}")

    def _export_selected_message(self):
        """Export the selected message."""
        current_item = self.message_list.currentItem()
        if current_item and self.current_collection:
            message_index = self.message_list.row(current_item)
            if 0 <= message_index < len(self.current_collection):
                message = self.current_collection[message_index]

                # For now, just show a placeholder
                QMessageBox.information(
                    self, "Export",
                    "Export functionality will be implemented in the Data Transformation task."
                )

    def _on_segment_selected(self, segment_name: str):
        """Handle segment selection in the segment grid."""
        if self.current_message and segment_name:
            # Find the segment in the current message
            for i, segment in enumerate(self.current_message.segments):
                if segment.name == segment_name:
                    self.current_segment_index = i
                    self._populate_segment_grid(segment)
                    break

    def _on_grid_item_changed(self, item: QTableWidgetItem):
        """Handle changes in the segment grid with validation."""
        if not self.current_message or self.current_segment_index < 0:
            return

        row = item.row()
        col = item.column()

        # Only handle value column changes (column 2)
        if col == 2:
            segment = self.current_message.segments[self.current_segment_index]
            field_number = row + 1  # Fields are 1-based
            new_value = item.text()

            # Get field definition for validation
            field_definitions = self.hl7_interpreter.field_definitions.get(segment.name, {})
            field_def = field_definitions.get(field_number)

            # Validate the new value
            validation_errors = []

            if field_def:
                # Check length constraints
                if field_def.max_length and len(new_value) > field_def.max_length:
                    validation_errors.append(f"Value exceeds maximum length of {field_def.max_length}")

                if field_def.min_length and len(new_value) < field_def.min_length:
                    validation_errors.append(f"Value is below minimum length of {field_def.min_length}")

                # Check required field
                if field_def.required and not new_value.strip():
                    validation_errors.append("Required field cannot be empty")

                # Validate against code table if applicable
                if field_def.table_id and new_value.strip():
                    table = self.hl7_interpreter.code_tables.get(field_def.table_id)
                    if table and not table.lookup(new_value.strip()):
                        validation_errors.append(f"Invalid code for table {field_def.table_id}")

            # Apply validation styling
            if validation_errors:
                item.setBackground(QColor(HL7SoupColors.ERROR_BACKGROUND))
                item.setToolTip("Validation errors:\n" + "\n".join(validation_errors))

                # Show validation message
                QMessageBox.warning(
                    self, "Validation Error",
                    f"Field {field_def.name if field_def else field_number} validation failed:\n" +
                    "\n".join(validation_errors)
                )
            else:
                # Clear validation styling
                if new_value.strip():
                    item.setBackground(QColor(HL7SoupColors.VALID_BACKGROUND))
                else:
                    item.setBackground(QColor())  # Default background
                item.setToolTip("")

            # Update the segment field
            segment.set_field(field_number, new_value)

            # Store raw value
            item.setData(Qt.ItemDataRole.UserRole, new_value)

            # Update display value with code interpretation
            if field_def and field_def.table_id and new_value.strip():
                table = self.hl7_interpreter.code_tables.get(field_def.table_id)
                if table:
                    code_desc = table.lookup(new_value.strip())
                    if code_desc:
                        item.setText(f"{new_value} ({code_desc})")

            # Update the editor
            self._update_editor_content()

            # Update interpretation panel
            self._update_interpretation_panel()

            # Mark as modified
            self._mark_as_modified()

            self.logger.debug(f"Updated field {segment.name}.{field_number} = '{new_value}'")

    def _on_grid_selection_changed(self):
        """Handle selection changes in the segment grid."""
        selected_items = self.segment_grid.selectedItems()
        if selected_items and self.current_message and self.current_segment_index >= 0:
            # Get the selected row
            row = selected_items[0].row()
            field_number = row + 1

            segment = self.current_message.segments[self.current_segment_index]
            field = segment.get_field(field_number)

            if field:
                # Update interpretation with field details
                self._update_interpretation_with_field(segment.name, field_number)

    def _show_grid_context_menu(self, position: QPoint):
        """Show context menu for segment grid."""
        item = self.segment_grid.itemAt(position)
        if not item:
            return

        row = item.row()
        col = item.column()

        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        # Field information
        if self.current_message and self.current_segment_index >= 0:
            segment = self.current_message.segments[self.current_segment_index]
            field_number = row + 1
            field = segment.get_field(field_number)

            field_definitions = self.hl7_interpreter.field_definitions.get(segment.name, {})
            field_def = field_definitions.get(field_number)

            if field_def:
                info_action = menu.addAction(f"Field Info: {field_def.name}")
                info_action.setEnabled(False)
                menu.addSeparator()

        # Edit actions (only for value column)
        if col == 2:
            copy_action = menu.addAction("Copy Value")
            copy_action.triggered.connect(lambda: self._copy_grid_value(row, col))

            paste_action = menu.addAction("Paste Value")
            paste_action.triggered.connect(lambda: self._paste_grid_value(row, col))

            clear_action = menu.addAction("Clear Value")
            clear_action.triggered.connect(lambda: self._clear_grid_value(row, col))

            menu.addSeparator()

        # Validation actions
        validate_field_action = menu.addAction("Validate Field")
        validate_field_action.triggered.connect(lambda: self._validate_grid_field(row))

        # Code lookup (if applicable)
        if col == 2 and self.current_message and self.current_segment_index >= 0:
            segment = self.current_message.segments[self.current_segment_index]
            field_number = row + 1
            field_definitions = self.hl7_interpreter.field_definitions.get(segment.name, {})
            field_def = field_definitions.get(field_number)

            if field_def and field_def.table_id:
                menu.addSeparator()
                lookup_action = menu.addAction(f"Code Lookup (Table {field_def.table_id})")
                lookup_action.triggered.connect(lambda: self._show_code_lookup(field_def.table_id))

        menu.exec(self.segment_grid.mapToGlobal(position))

    def _copy_grid_value(self, row: int, col: int):
        """Copy grid value to clipboard."""
        item = self.segment_grid.item(row, col)
        if item:
            # Get raw value if available
            raw_value = item.data(Qt.ItemDataRole.UserRole)
            if raw_value is not None:
                QApplication.clipboard().setText(str(raw_value))
            else:
                QApplication.clipboard().setText(item.text())

    def _paste_grid_value(self, row: int, col: int):
        """Paste value from clipboard to grid."""
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text:
            item = self.segment_grid.item(row, col)
            if item:
                item.setText(clipboard_text)
                # Trigger the change handler
                self._on_grid_item_changed(item)

    def _clear_grid_value(self, row: int, col: int):
        """Clear grid value."""
        item = self.segment_grid.item(row, col)
        if item:
            item.setText("")
            # Trigger the change handler
            self._on_grid_item_changed(item)

    def _validate_grid_field(self, row: int):
        """Validate a specific field in the grid."""
        if not self.current_message or self.current_segment_index < 0:
            return

        segment = self.current_message.segments[self.current_segment_index]
        field_number = row + 1
        field = segment.get_field(field_number)

        if field:
            # Get field definition
            field_definitions = self.hl7_interpreter.field_definitions.get(segment.name, {})
            field_def = field_definitions.get(field_number)

            # Perform validation
            validation_results = []
            field_value = field.get_value()

            if field_def:
                if field_def.required and not field_value.strip():
                    validation_results.append("Required field is empty")

                if field_def.max_length and len(field_value) > field_def.max_length:
                    validation_results.append(f"Exceeds maximum length of {field_def.max_length}")

                if field_def.table_id and field_value.strip():
                    table = self.hl7_interpreter.code_tables.get(field_def.table_id)
                    if table and not table.lookup(field_value.strip()):
                        validation_results.append(f"Invalid code for table {field_def.table_id}")

            # Show results
            if validation_results:
                QMessageBox.warning(
                    self, "Field Validation",
                    f"Field {field_def.name if field_def else field_number} validation:\n" +
                    "\n".join(validation_results)
                )
            else:
                QMessageBox.information(
                    self, "Field Validation",
                    f"Field {field_def.name if field_def else field_number} is valid."
                )

    def _show_code_lookup(self, table_id: str):
        """Show code lookup dialog for a table."""
        table = self.hl7_interpreter.code_tables.get(table_id)
        if table:
            # Create a simple dialog showing available codes
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Code Lookup - Table {table_id}: {table.name}")
            dialog.setModal(True)
            dialog.resize(500, 400)

            layout = QVBoxLayout(dialog)

            list_widget = QListWidget()
            for code, description in sorted(table.codes.items()):
                list_widget.addItem(f"{code} - {description}")

            layout.addWidget(list_widget)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)

            dialog.exec()

    def _filter_messages(self):
        """Filter messages based on current filter settings with enhanced options."""
        if not self.current_collection:
            return

        filter_text = self.filter_input.text().strip()
        filter_type = self.filter_type_combo.currentText()

        self.message_list.clear()

        if not filter_text:
            # Show all messages
            self._populate_message_list(self.current_collection.messages)
        else:
            # Filter messages with enhanced logic
            filtered_messages = []

            for message in self.current_collection.messages:
                match = False
                filter_lower = filter_text.lower()

                if filter_type == "All" or filter_type == "Content":
                    if filter_lower in str(message).lower():
                        match = True

                elif filter_type == "Type":
                    if filter_lower in message.get_message_type().lower():
                        match = True

                elif filter_type == "Control ID":
                    if filter_lower in message.get_control_id().lower():
                        match = True

                elif filter_type == "Segment":
                    # Check if any segment name matches
                    for segment in message.segments:
                        if filter_lower in segment.name.lower():
                            match = True
                            break

                elif filter_type == "Field Value":
                    # Check field values
                    for segment in message.segments:
                        for field in segment.fields:
                            if filter_lower in field.get_value().lower():
                                match = True
                                break
                        if match:
                            break

                elif filter_type == "Validation Status":
                    # Filter by validation status
                    if filter_lower == "error" and message.has_errors():
                        match = True
                    elif filter_lower == "warning" and message.has_warnings():
                        match = True
                    elif filter_lower == "valid" and message.is_valid():
                        match = True

                elif filter_type == "Message Size":
                    # Filter by message size (number of segments)
                    try:
                        size_filter = int(filter_text)
                        if len(message.segments) >= size_filter:
                            match = True
                    except ValueError:
                        # If not a number, check size ranges
                        if filter_lower == "small" and len(message.segments) <= 5:
                            match = True
                        elif filter_lower == "medium" and 6 <= len(message.segments) <= 15:
                            match = True
                        elif filter_lower == "large" and len(message.segments) > 15:
                            match = True

                if match:
                    filtered_messages.append(message)

            self._populate_message_list(filtered_messages)

        # Update count
        visible_count = self.message_list.count()
        total_count = len(self.current_collection.messages)
        if visible_count == total_count:
            self.message_count_label.setText(f"{total_count} messages")
        else:
            self.message_count_label.setText(f"{visible_count} of {total_count} messages")

    def _on_segment_clicked(self, segment_name: str, line_number: int):
        """Handle segment click in editor."""
        self.logger.debug(f"Segment clicked: {segment_name} at line {line_number}")

        # Update segment selector
        index = self.segment_selector.findText(segment_name)
        if index >= 0:
            self.segment_selector.setCurrentIndex(index)

        # Update interpretation with segment info
        self._update_interpretation_with_segment(segment_name, line_number)

    def _on_field_clicked(self, segment_name: str, line_number: int, field_number: int):
        """Handle field click in editor."""
        self.logger.debug(f"Field clicked: {segment_name}.{field_number} at line {line_number}")

        # Highlight the field in the segment grid
        if self.current_segment_index >= 0:
            self.segment_grid.selectRow(field_number - 1)

        # Update interpretation with field info
        self._update_interpretation_with_field(segment_name, field_number)

    def _on_editor_content_changed(self):
        """Handle editor content changes."""
        # Mark as modified
        self._mark_as_modified()

        # Parse the content and update current message
        current_editor = self.editor_tabs.currentWidget()
        if current_editor and isinstance(current_editor, HL7TextEditor):
            content = current_editor.get_hl7_content()
            if content.strip():
                try:
                    # Parse the content
                    message = self.hl7_parser.parse_message(content)
                    if message:
                        current_editor.hl7_message = message
                        self.current_message = message

                        # Update other panels
                        self._update_interpretation_panel()
                        self._update_segment_grid()
                except Exception as e:
                    self.logger.debug(f"Failed to parse editor content: {e}")

    def _update_interpretation_with_segment(self, segment_name: str, line_number: int):
        """Update interpretation panel with segment-specific information."""
        if not self.current_message:
            return

        # Find the segment
        segment = None
        for seg in self.current_message.segments:
            if seg.name == segment_name:
                segment = seg
                break

        if segment:
            # Use interpreter for segment-specific interpretation
            segment_interpretation = self.hl7_interpreter.interpret_segment(segment)

            # Add to existing interpretation
            current_html = self.interpretation_text.toHtml()
            self.interpretation_text.setHtml(current_html + "<hr>" + segment_interpretation)

    def _update_interpretation_with_field(self, segment_name: str, field_number: int):
        """Update interpretation panel with field-specific information."""
        if not self.current_message:
            return

        # Find the segment and field
        for segment in self.current_message.segments:
            if segment.name == segment_name:
                field = segment.get_field(field_number)
                if field:
                    # Use interpreter for field-specific interpretation
                    field_interpretation = self.hl7_interpreter.interpret_field(segment_name, field_number, field)

                    # Add to existing interpretation
                    current_html = self.interpretation_text.toHtml()
                    self.interpretation_text.setHtml(current_html + "<hr>" + field_interpretation)
                break
    
    # File Operations
    def _new_message(self):
        """Create a new HL7 message."""
        # Add a new editor tab with empty content
        editor = self._add_editor_tab("New Message")
        editor.setPlainText("MSH|^~\\&||||||||||||")
        editor.setFocus()

    def _open_file(self):
        """Open an HL7 file with validation."""
        # Build filter string from supported extensions
        extensions = self.file_manager.get_supported_extensions()
        ext_filter = " ".join(f"*{ext}" for ext in extensions)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open HL7 File",
            "",
            f"HL7 Files ({ext_filter});;All Files (*)"
        )

        if file_path:
            # Validate file before loading
            file_info = self.file_manager.get_file_info(file_path)

            if not file_info['is_valid_hl7']:
                # Show validation issues
                issues_text = "\n".join(file_info['issues'])
                reply = QMessageBox.question(
                    self, "File Validation",
                    f"The selected file may not be a valid HL7 file:\n\n{issues_text}\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    return

            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """Load an HL7 file."""
        try:
            self.status_bar.showMessage(f"Loading {file_path}...")
            QApplication.processEvents()

            # Parse the file
            collection = self.hl7_parser.parse_file(file_path)
            self.current_collection = collection

            # Update UI
            self._populate_message_list(collection.messages)

            # Load first message in editor if available
            if collection.messages:
                self._load_message_in_editor(collection.messages[0])

            # Update window title
            self.setWindowTitle(f"HL7 OpenSoup - {file_path}")

            # Add to recent files
            self.config.add_recent_file(file_path)
            self._update_recent_files_menu()

            # Enable actions
            self.save_action.setEnabled(True)
            self.save_as_action.setEnabled(True)
            self.validate_action.setEnabled(True)
            self.export_action.setEnabled(True)

            self.status_bar.showMessage(f"Loaded {len(collection.messages)} messages from {file_path}")
            self.logger.info(f"Loaded file: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            self.status_bar.showMessage("Ready")
            self.logger.error(f"Failed to load file {file_path}: {e}")

    def _save_file(self):
        """Save the current file."""
        if self.current_collection and self.current_collection.file_path:
            self._save_to_file(self.current_collection.file_path)
        else:
            self._save_file_as()

    def _save_file_as(self):
        """Save the current file with a new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HL7 File",
            "",
            "HL7 Files (*.hl7);;Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            self._save_to_file(file_path)

    def _save_to_file(self, file_path: str):
        """Save messages to a file with validation and backup."""
        try:
            if not self.current_collection:
                return

            self.status_bar.showMessage(f"Saving {file_path}...")
            QApplication.processEvents()

            # Collect all message content
            content_lines = []
            for message in self.current_collection.messages:
                content_lines.append(str(message))

            content = '\n\n'.join(content_lines)

            # Use file manager for safe writing
            if self.file_manager.safe_write_file(file_path, content):
                # Update collection
                self.current_collection.file_path = file_path

                # Update window title (remove * if present)
                title = f"HL7 OpenSoup - {file_path}"
                self.setWindowTitle(title)

                # Add to recent files
                self.config.add_recent_file(file_path)
                self._update_recent_files_menu()

                self.status_bar.showMessage(f"Saved {file_path}")
                self.logger.info(f"Saved file: {file_path}")
            else:
                raise Exception("File manager failed to write file")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
            self.status_bar.showMessage("Ready")
            self.logger.error(f"Failed to save file {file_path}: {e}")

    def _auto_save(self):
        """Auto-save current work."""
        if self.current_collection and self.current_collection.file_path:
            self._save_to_file(self.current_collection.file_path)

    def _mark_as_modified(self):
        """Mark the current document as modified."""
        title = self.windowTitle()
        if not title.endswith("*"):
            self.setWindowTitle(title + "*")

    def closeEvent(self, event):
        """Handle application close event."""
        # Save window geometry and state
        self.config.set('ui.window_geometry', self.saveGeometry())
        self.config.set('ui.window_state', self.saveState())
        self.config.save_config()

        self.logger.info("Application closing")
        event.accept()

    # UI Update Methods
    def _populate_message_list(self, messages: list):
        """Populate the message list with messages."""
        self.message_list.clear()

        for i, message in enumerate(messages):
            # Create list item with HL7 Soup style formatting
            msg_type = message.get_message_type()
            control_id = message.get_control_id()

            # Format like HL7 Soup: "1. ADT^A01 (12345)"
            item_text = f"{i+1:3d}. {msg_type}"
            if control_id:
                item_text += f" ({control_id})"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i)  # Store original index

            # Set font to monospace for consistent alignment
            font = QFont("Courier New", 10)
            item.setFont(font)

            # Color code based on validation status using HL7 Soup colors
            if message.has_errors():
                item.setBackground(QColor(HL7SoupColors.ERROR_BACKGROUND))
                item.setData(Qt.ItemDataRole.UserRole + 1, "error")
            elif message.has_warnings():
                item.setBackground(QColor(HL7SoupColors.WARNING_BACKGROUND))
                item.setData(Qt.ItemDataRole.UserRole + 1, "warning")
            else:
                item.setBackground(QColor(HL7SoupColors.VALID_BACKGROUND))
                item.setData(Qt.ItemDataRole.UserRole + 1, "valid")

            # Add tooltip with message details
            tooltip_text = f"Message Type: {msg_type}\n"
            tooltip_text += f"Control ID: {control_id}\n"
            tooltip_text += f"Segments: {len(message.segments)}\n"
            if message.validation_results:
                error_count = len([r for r in message.validation_results if r.level.value == "error"])
                warning_count = len([r for r in message.validation_results if r.level.value == "warning"])
                tooltip_text += f"Validation: {error_count} errors, {warning_count} warnings"
            else:
                tooltip_text += "Validation: Not validated"
            item.setToolTip(tooltip_text)

            self.message_list.addItem(item)

        # Update count with HL7 Soup style
        total_count = len(messages)
        if self.current_collection:
            all_count = len(self.current_collection.messages)
            if total_count == all_count:
                self.message_count_label.setText(f"{total_count} messages")
            else:
                self.message_count_label.setText(f"{total_count} of {all_count} messages")
        else:
            self.message_count_label.setText(f"{total_count} messages")

    def _load_message_in_editor(self, message: HL7Message):
        """Load a message in the editor."""
        self.current_message = message

        # Find or create editor tab
        current_editor = self.editor_tabs.currentWidget()
        if current_editor and isinstance(current_editor, HL7TextEditor):
            current_editor.set_hl7_message(message)
        else:
            editor = self._add_editor_tab(f"Message {message.get_control_id()}")
            editor.set_hl7_message(message)

        # Update other panels
        self._update_interpretation_panel()
        self._update_segment_grid()

    def _update_interpretation_panel(self):
        """Update the interpretation panel with current message info."""
        if not self.current_message:
            self.interpretation_text.clear()
            return

        # Use the interpreter to generate comprehensive interpretation
        interpretation = self.hl7_interpreter.interpret_message(self.current_message)
        self.interpretation_text.setHtml(interpretation)

    def _update_segment_grid(self):
        """Update the segment grid with current message segments."""
        self.segment_selector.clear()

        if not self.current_message:
            self.segment_grid.setRowCount(0)
            return

        # Populate segment selector
        for segment in self.current_message.segments:
            self.segment_selector.addItem(segment.name)

        # Load first segment if available
        if self.current_message.segments:
            self.current_segment_index = 0
            self._populate_segment_grid(self.current_message.segments[0])

    def _populate_segment_grid(self, segment):
        """Populate the segment grid with segment fields."""
        self.segment_grid.setRowCount(len(segment.fields))

        # Get field definitions from interpreter
        field_definitions = self.hl7_interpreter.field_definitions.get(segment.name, {})

        for i, field in enumerate(segment.fields):
            field_number = i + 1

            # Field number with validation indicator
            field_item = QTableWidgetItem(str(field_number))
            field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Add validation indicator for required fields
            field_def = field_definitions.get(field_number)
            if field_def and field_def.required and field.is_empty():
                field_item.setBackground(QColor(HL7SoupColors.ERROR_BACKGROUND))
                field_item.setToolTip("Required field is empty")

            self.segment_grid.setItem(i, 0, field_item)

            # Field name from interpreter with indicators
            if field_def:
                name_text = field_def.name
                if field_def.required:
                    name_text += " *"
                if field_def.repeatable:
                    name_text += " (R)"

                # Add data type info
                if field_def.data_type:
                    name_text += f" [{field_def.data_type}]"
            else:
                name_text = f"Field {field_number}"

            name_item = QTableWidgetItem(name_text)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Color code by field type
            if field_def:
                if field_def.required:
                    name_item.setForeground(QColor("#000080"))  # Blue for required
                    name_item.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
                else:
                    name_item.setForeground(QColor("#000000"))  # Black for optional

            self.segment_grid.setItem(i, 1, name_item)

            # Field value with enhanced display
            raw_value = str(field)
            display_value = raw_value

            # Show code interpretation if available
            if field_def and field_def.table_id and raw_value:
                table = self.hl7_interpreter.code_tables.get(field_def.table_id)
                if table:
                    code_desc = table.lookup(raw_value)
                    if code_desc:
                        display_value = f"{raw_value} ({code_desc})"

            value_item = QTableWidgetItem(display_value)

            # Store raw value for editing
            value_item.setData(Qt.ItemDataRole.UserRole, raw_value)

            # Validation styling for value
            if field_def:
                # Check field length
                if field_def.max_length and len(raw_value) > field_def.max_length:
                    value_item.setBackground(QColor(HL7SoupColors.WARNING_BACKGROUND))
                    value_item.setToolTip(f"Value exceeds maximum length of {field_def.max_length}")
                elif field_def.required and field.is_empty():
                    value_item.setBackground(QColor(HL7SoupColors.ERROR_BACKGROUND))
                    value_item.setToolTip("Required field is empty")
                elif raw_value:
                    value_item.setBackground(QColor(HL7SoupColors.VALID_BACKGROUND))

            # Set font for value
            value_font = QFont("Courier New", 10)
            value_item.setFont(value_font)

            self.segment_grid.setItem(i, 2, value_item)

            # Field description with enhanced info
            if field_def:
                desc_text = field_def.description
                if field_def.table_id:
                    desc_text += f" (Table {field_def.table_id})"
                if field_def.max_length:
                    desc_text += f" [Max: {field_def.max_length}]"
            else:
                desc_text = "Field description not available"

            desc_item = QTableWidgetItem(desc_text)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            desc_item.setFont(QFont("Segoe UI", 9))
            self.segment_grid.setItem(i, 3, desc_item)

        # Auto-resize columns for better display
        self.segment_grid.resizeColumnsToContents()

        # Ensure value column is still stretchable
        header = self.segment_grid.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def _update_editor_content(self):
        """Update the editor content with current message."""
        if self.current_message:
            current_editor = self.editor_tabs.currentWidget()
            if current_editor:
                current_editor.setPlainText(str(self.current_message))

    # Menu Action Handlers
    def _copy_text(self):
        """Copy selected text to clipboard."""
        current_editor = self.editor_tabs.currentWidget()
        if current_editor and hasattr(current_editor, 'copy'):
            current_editor.copy()

    def _paste_text(self):
        """Paste text from clipboard."""
        current_editor = self.editor_tabs.currentWidget()
        if current_editor and hasattr(current_editor, 'paste'):
            current_editor.paste()

    def _show_find_dialog(self):
        """Show simple find dialog."""
        # Focus on the filter input for quick search
        self.filter_input.setFocus()
        self.filter_input.selectAll()

    def _show_advanced_search(self):
        """Show advanced search dialog."""
        if not self.current_collection:
            QMessageBox.information(
                self, "Advanced Search",
                "Please open an HL7 file first to enable search functionality."
            )
            return

        # Create or show search dialog
        if not self.search_dialog:
            self.search_dialog = AdvancedSearchDialog(self.current_collection, self)
            self.search_dialog.result_selected.connect(self._on_search_result_selected)
            self.search_dialog.search_performed.connect(self._on_search_performed)
        else:
            # Update collection in case it changed
            self.search_dialog.collection = self.current_collection

        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def _on_search_result_selected(self, result):
        """Handle search result selection."""
        # Navigate to the selected message
        if 0 <= result.message_index < len(self.current_collection.messages):
            # Select message in list
            self.message_list.setCurrentRow(result.message_index)

            # Load message in editor
            message = self.current_collection.messages[result.message_index]
            self._load_message_in_editor(message)

            # If specific segment/field, navigate to it
            if result.segment_index >= 0:
                # Update segment selector
                if result.segment_index < len(message.segments):
                    segment_name = message.segments[result.segment_index].name
                    index = self.segment_selector.findText(segment_name)
                    if index >= 0:
                        self.segment_selector.setCurrentIndex(index)

                    # If specific field, select it in grid
                    if result.field_index >= 0:
                        self.segment_grid.selectRow(result.field_index)

            # Update status
            self.status_bar.showMessage(f"Navigated to search result: {result}")

    def _on_search_performed(self, results):
        """Handle search completion."""
        count = len(results)
        self.status_bar.showMessage(f"Search completed: {count} result{'s' if count != 1 else ''} found")

    def _refresh_view(self):
        """Refresh the current view."""
        if self.current_message:
            self._update_interpretation_panel()
            self._update_segment_grid()

    def _validate_message(self):
        """Validate the current message."""
        if not self.current_message:
            return

        try:
            self.status_bar.showMessage("Validating message...")
            QApplication.processEvents()

            # Validate the message
            results = self.hl7_validator.validate_message(self.current_message)

            # Update interpretation panel
            self._update_interpretation_panel()

            # Show summary
            error_count = len([r for r in results if r.level.value == "error"])
            warning_count = len([r for r in results if r.level.value == "warning"])

            if error_count == 0 and warning_count == 0:
                QMessageBox.information(self, "Validation", "Message is valid!")
            else:
                msg = f"Validation completed:\n{error_count} errors, {warning_count} warnings"
                QMessageBox.warning(self, "Validation", msg)

            self.status_bar.showMessage("Validation completed")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Validation failed:\n{e}")
            self.status_bar.showMessage("Ready")

    def _export_message(self):
        """Export current message to different format."""
        if not self.current_message:
            return

        # This would open an export dialog
        QMessageBox.information(self, "Export", "Export functionality will be implemented in the next task.")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About HL7 OpenSoup",
            "HL7 OpenSoup v1.0.0\n\n"
            "Advanced HL7 Desktop Viewer and Editor\n"
            "A Python-based replica of HL7 Soup\n\n"
            "Built with PyQt6 and Python"
        )

    def _update_recent_files_menu(self):
        """Update the recent files menu."""
        self.recent_menu.clear()

        recent_files = self.config.get_recent_files()

        if not recent_files:
            action = self.recent_menu.addAction("No recent files")
            action.setEnabled(False)
        else:
            for file_path in recent_files[:10]:  # Show last 10 files
                action = self.recent_menu.addAction(file_path)
                action.triggered.connect(lambda checked, path=file_path: self._load_file(path))
