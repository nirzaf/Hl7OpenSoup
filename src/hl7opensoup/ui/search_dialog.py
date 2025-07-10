"""
Advanced Search Dialog for HL7 OpenSoup.

This module provides an advanced search dialog with regex support,
highlighting, and filtering capabilities similar to HL7 Soup.
"""

import re
import logging
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QTextEdit, QListWidget, QTabWidget,
    QWidget, QGroupBox, QSpinBox, QDialogButtonBox, QListWidgetItem,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

from hl7opensoup.models.hl7_message import HL7Message, HL7MessageCollection
from hl7opensoup.ui.hl7_soup_style import HL7SoupColors, get_panel_title_style


class SearchResult:
    """Represents a search result."""
    
    def __init__(self, message_index: int, message: HL7Message, 
                 segment_index: int = -1, field_index: int = -1,
                 match_text: str = "", line_number: int = -1):
        """Initialize search result.
        
        Args:
            message_index: Index of message in collection
            message: The HL7 message
            segment_index: Index of segment in message (-1 if not specific)
            field_index: Index of field in segment (-1 if not specific)
            match_text: The matching text
            line_number: Line number in message (-1 if not specific)
        """
        self.message_index = message_index
        self.message = message
        self.segment_index = segment_index
        self.field_index = field_index
        self.match_text = match_text
        self.line_number = line_number
    
    def __str__(self) -> str:
        """String representation of search result."""
        msg_type = self.message.get_message_type()
        control_id = self.message.get_control_id()
        
        result = f"Message {self.message_index + 1}: {msg_type}"
        if control_id:
            result += f" ({control_id})"
        
        if self.segment_index >= 0:
            segment_name = self.message.segments[self.segment_index].name
            result += f" -> {segment_name}"
            
            if self.field_index >= 0:
                result += f".{self.field_index + 1}"
        
        if self.line_number >= 0:
            result += f" [Line {self.line_number}]"
        
        if self.match_text:
            result += f": {self.match_text[:50]}..."
        
        return result


class AdvancedSearchDialog(QDialog):
    """Advanced search dialog with regex and filtering support."""
    
    # Signals
    search_performed = pyqtSignal(list)  # List of SearchResult objects
    result_selected = pyqtSignal(object)  # SearchResult object
    
    def __init__(self, collection: HL7MessageCollection, parent=None):
        """Initialize the search dialog.
        
        Args:
            collection: HL7 message collection to search
            parent: Parent widget
        """
        super().__init__(parent)
        self.collection = collection
        self.logger = logging.getLogger(__name__)
        self.search_results: List[SearchResult] = []
        
        self.setWindowTitle("Advanced Search - HL7 OpenSoup")
        self.setModal(False)  # Allow interaction with main window
        self.resize(800, 600)
        
        self._setup_ui()
        self._connect_signals()
        
        # Auto-search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Search criteria panel
        search_panel = self._create_search_panel()
        splitter.addWidget(search_panel)
        
        # Results panel
        results_panel = self._create_results_panel()
        splitter.addWidget(results_panel)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close |
            QDialogButtonBox.StandardButton.Help
        )
        button_box.rejected.connect(self.close)
        button_box.helpRequested.connect(self._show_help)
        layout.addWidget(button_box)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 300])
    
    def _create_search_panel(self) -> QWidget:
        """Create the search criteria panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet(f"background-color: {HL7SoupColors.PANEL_BACKGROUND};")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("Search Criteria")
        title_label.setStyleSheet(get_panel_title_style())
        layout.addWidget(title_label)
        
        # Search input
        search_layout = QGridLayout()
        
        search_layout.addWidget(QLabel("Search for:"), 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term or regex pattern...")
        search_layout.addWidget(self.search_input, 0, 1, 1, 2)
        
        # Search options
        search_layout.addWidget(QLabel("Search in:"), 1, 0)
        self.search_scope = QComboBox()
        self.search_scope.addItems([
            "All Content",
            "Message Type",
            "Control ID",
            "Segment Names",
            "Field Values",
            "Specific Segment",
            "Specific Field"
        ])
        search_layout.addWidget(self.search_scope, 1, 1)
        
        # Regex checkbox
        self.regex_checkbox = QCheckBox("Use Regular Expressions")
        search_layout.addWidget(self.regex_checkbox, 1, 2)
        
        # Case sensitive checkbox
        self.case_sensitive_checkbox = QCheckBox("Case Sensitive")
        search_layout.addWidget(self.case_sensitive_checkbox, 2, 0)
        
        # Whole word checkbox
        self.whole_word_checkbox = QCheckBox("Whole Words Only")
        search_layout.addWidget(self.whole_word_checkbox, 2, 1)
        
        # Auto-search checkbox
        self.auto_search_checkbox = QCheckBox("Search as you type")
        self.auto_search_checkbox.setChecked(True)
        search_layout.addWidget(self.auto_search_checkbox, 2, 2)
        
        layout.addLayout(search_layout)
        
        # Specific segment/field options
        specific_layout = QHBoxLayout()
        
        specific_layout.addWidget(QLabel("Segment:"))
        self.segment_input = QLineEdit()
        self.segment_input.setPlaceholderText("e.g., PID, MSH")
        self.segment_input.setMaximumWidth(80)
        self.segment_input.setEnabled(False)
        specific_layout.addWidget(self.segment_input)
        
        specific_layout.addWidget(QLabel("Field:"))
        self.field_input = QSpinBox()
        self.field_input.setMinimum(1)
        self.field_input.setMaximum(999)
        self.field_input.setEnabled(False)
        specific_layout.addWidget(self.field_input)
        
        specific_layout.addStretch()
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setDefault(True)
        specific_layout.addWidget(self.search_button)
        
        layout.addLayout(specific_layout)
        
        return panel
    
    def _create_results_panel(self) -> QWidget:
        """Create the search results panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet(f"background-color: {HL7SoupColors.PANEL_BACKGROUND};")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title with count
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Search Results")
        title_label.setStyleSheet(get_panel_title_style())
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        self.results_count_label = QLabel("0 results")
        self.results_count_label.setStyleSheet(f"""
            color: {HL7SoupColors.TEXT_DISABLED};
            font-size: 10px;
            font-style: italic;
        """)
        title_layout.addWidget(self.results_count_label)
        
        layout.addLayout(title_layout)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                font-family: "Courier New", "Consolas", monospace;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.results_list)
        
        return panel
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_scope.currentTextChanged.connect(self._on_scope_changed)
        self.search_button.clicked.connect(self._perform_search)
        self.results_list.itemDoubleClicked.connect(self._on_result_double_clicked)
        self.results_list.itemSelectionChanged.connect(self._on_result_selected)
    
    def _on_search_text_changed(self):
        """Handle search text changes."""
        if self.auto_search_checkbox.isChecked():
            # Start timer for auto-search
            self.search_timer.start(500)  # 500ms delay
    
    def _on_scope_changed(self, scope: str):
        """Handle search scope changes."""
        # Enable/disable specific segment/field inputs
        enable_specific = scope in ["Specific Segment", "Specific Field"]
        self.segment_input.setEnabled(enable_specific)
        self.field_input.setEnabled(scope == "Specific Field")
        
        # Trigger search if auto-search is enabled
        if self.auto_search_checkbox.isChecked():
            self.search_timer.start(500)
    
    def _perform_search(self):
        """Perform the search operation."""
        search_term = self.search_input.text().strip()
        if not search_term:
            self._clear_results()
            return
        
        try:
            self.search_results = self._search_collection(search_term)
            self._populate_results()
            self.search_performed.emit(self.search_results)
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            self._clear_results()
            self.results_count_label.setText(f"Search error: {e}")
    
    def _search_collection(self, search_term: str) -> List[SearchResult]:
        """Search the message collection.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of search results
        """
        results = []
        scope = self.search_scope.currentText()
        use_regex = self.regex_checkbox.isChecked()
        case_sensitive = self.case_sensitive_checkbox.isChecked()
        whole_word = self.whole_word_checkbox.isChecked()
        
        # Prepare search pattern
        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(search_term, flags)
            except re.error as e:
                raise Exception(f"Invalid regex pattern: {e}")
        else:
            # Escape special regex characters
            escaped_term = re.escape(search_term)
            if whole_word:
                escaped_term = r'\b' + escaped_term + r'\b'
            
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(escaped_term, flags)
        
        # Search through messages
        for msg_idx, message in enumerate(self.collection.messages):
            if scope == "All Content":
                results.extend(self._search_message_content(msg_idx, message, pattern))
            elif scope == "Message Type":
                results.extend(self._search_message_type(msg_idx, message, pattern))
            elif scope == "Control ID":
                results.extend(self._search_control_id(msg_idx, message, pattern))
            elif scope == "Segment Names":
                results.extend(self._search_segment_names(msg_idx, message, pattern))
            elif scope == "Field Values":
                results.extend(self._search_field_values(msg_idx, message, pattern))
            elif scope == "Specific Segment":
                results.extend(self._search_specific_segment(msg_idx, message, pattern))
            elif scope == "Specific Field":
                results.extend(self._search_specific_field(msg_idx, message, pattern))
        
        return results
    
    def _search_message_content(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search entire message content."""
        results = []
        content = str(message)
        
        for match in pattern.finditer(content):
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            match_text = match.group()
            
            results.append(SearchResult(
                msg_idx, message, -1, -1, match_text, line_num
            ))
        
        return results
    
    def _search_message_type(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search message type."""
        results = []
        msg_type = message.get_message_type()
        
        if pattern.search(msg_type):
            results.append(SearchResult(
                msg_idx, message, -1, -1, msg_type
            ))
        
        return results
    
    def _search_control_id(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search control ID."""
        results = []
        control_id = message.get_control_id()
        
        if pattern.search(control_id):
            results.append(SearchResult(
                msg_idx, message, -1, -1, control_id
            ))
        
        return results
    
    def _search_segment_names(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search segment names."""
        results = []
        
        for seg_idx, segment in enumerate(message.segments):
            if pattern.search(segment.name):
                results.append(SearchResult(
                    msg_idx, message, seg_idx, -1, segment.name
                ))
        
        return results
    
    def _search_field_values(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search field values."""
        results = []
        
        for seg_idx, segment in enumerate(message.segments):
            for field_idx, field in enumerate(segment.fields):
                field_value = field.get_value()
                if pattern.search(field_value):
                    results.append(SearchResult(
                        msg_idx, message, seg_idx, field_idx, field_value
                    ))
        
        return results
    
    def _search_specific_segment(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search within a specific segment type."""
        results = []
        target_segment = self.segment_input.text().strip().upper()
        
        if not target_segment:
            return results
        
        for seg_idx, segment in enumerate(message.segments):
            if segment.name == target_segment:
                segment_content = str(segment)
                if pattern.search(segment_content):
                    results.append(SearchResult(
                        msg_idx, message, seg_idx, -1, segment_content[:100]
                    ))
        
        return results
    
    def _search_specific_field(self, msg_idx: int, message: HL7Message, pattern: re.Pattern) -> List[SearchResult]:
        """Search within a specific field."""
        results = []
        target_segment = self.segment_input.text().strip().upper()
        target_field = self.field_input.value()
        
        if not target_segment:
            return results
        
        for seg_idx, segment in enumerate(message.segments):
            if segment.name == target_segment:
                field = segment.get_field(target_field)
                if field:
                    field_value = field.get_value()
                    if pattern.search(field_value):
                        results.append(SearchResult(
                            msg_idx, message, seg_idx, target_field - 1, field_value
                        ))
        
        return results
    
    def _populate_results(self):
        """Populate the results list."""
        self.results_list.clear()
        
        for result in self.search_results:
            item = QListWidgetItem(str(result))
            item.setData(Qt.ItemDataRole.UserRole, result)
            
            # Set font
            font = QFont("Courier New", 10)
            item.setFont(font)
            
            self.results_list.addItem(item)
        
        # Update count
        count = len(self.search_results)
        self.results_count_label.setText(f"{count} result{'s' if count != 1 else ''}")
    
    def _clear_results(self):
        """Clear search results."""
        self.results_list.clear()
        self.search_results.clear()
        self.results_count_label.setText("0 results")
    
    def _on_result_selected(self):
        """Handle result selection."""
        current_item = self.results_list.currentItem()
        if current_item:
            result = current_item.data(Qt.ItemDataRole.UserRole)
            self.result_selected.emit(result)
    
    def _on_result_double_clicked(self, item: QListWidgetItem):
        """Handle result double-click."""
        result = item.data(Qt.ItemDataRole.UserRole)
        if result:
            self.result_selected.emit(result)
            # Optionally close dialog
            # self.accept()
    
    def _show_help(self):
        """Show search help."""
        from PyQt6.QtWidgets import QMessageBox
        
        help_text = """
Advanced Search Help:

Search Scopes:
• All Content - Search entire message content
• Message Type - Search message type field (MSH.9)
• Control ID - Search message control ID (MSH.10)
• Segment Names - Search segment names only
• Field Values - Search all field values
• Specific Segment - Search within specific segment type
• Specific Field - Search specific field in specific segment

Regular Expressions:
When enabled, you can use regex patterns:
• .* - Match any characters
• \\d+ - Match one or more digits
• ^MSH - Match lines starting with MSH
• PID|NK1 - Match PID or NK1

Options:
• Case Sensitive - Match exact case
• Whole Words Only - Match complete words
• Search as you type - Auto-search while typing
        """
        
        QMessageBox.information(self, "Search Help", help_text.strip())
