"""
HL7 Message Editor with Syntax Highlighting for HL7 OpenSoup.

This module provides a specialized text editor for HL7 messages with
syntax highlighting, line numbers, and hyperlink detection.
"""

import re
import logging
from typing import Optional, List, Dict, Tuple

from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollBar, QApplication, QToolTip
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import (
    QColor, QTextCharFormat, QFont, QPainter, QTextCursor,
    QSyntaxHighlighter, QTextDocument, QPalette, QMouseEvent,
    QKeyEvent, QWheelEvent
)

from hl7opensoup.models.hl7_message import HL7Message, HL7Separators
from hl7opensoup.ui.hl7_soup_style import HL7SoupColors


class HL7SyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for HL7 messages."""
    
    def __init__(self, parent: QTextDocument):
        """Initialize the syntax highlighter.
        
        Args:
            parent: Parent text document
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Define highlighting rules
        self._setup_highlighting_rules()
    
    def _setup_highlighting_rules(self):
        """Set up syntax highlighting rules using HL7 Soup colors."""
        # Segment name format (first 3 characters of each line)
        self.segment_format = QTextCharFormat()
        self.segment_format.setForeground(QColor(HL7SoupColors.SEGMENT_COLOR))
        self.segment_format.setFontWeight(QFont.Weight.Bold)

        # Field separator format
        self.field_separator_format = QTextCharFormat()
        self.field_separator_format.setForeground(QColor(HL7SoupColors.FIELD_SEP_COLOR))
        self.field_separator_format.setFontWeight(QFont.Weight.Bold)

        # Component separator format
        self.component_separator_format = QTextCharFormat()
        self.component_separator_format.setForeground(QColor(HL7SoupColors.COMPONENT_SEP_COLOR))

        # Repetition separator format
        self.repetition_separator_format = QTextCharFormat()
        self.repetition_separator_format.setForeground(QColor(HL7SoupColors.REPETITION_SEP_COLOR))

        # Subcomponent separator format
        self.subcomponent_separator_format = QTextCharFormat()
        self.subcomponent_separator_format.setForeground(QColor(HL7SoupColors.SUBCOMP_SEP_COLOR))

        # Escape character format
        self.escape_format = QTextCharFormat()
        self.escape_format.setForeground(QColor(HL7SoupColors.ESCAPE_COLOR))
        self.escape_format.setFontWeight(QFont.Weight.Bold)

        # MSH encoding characters format
        self.encoding_chars_format = QTextCharFormat()
        self.encoding_chars_format.setForeground(QColor(HL7SoupColors.ENCODING_CHARS_COLOR))
        self.encoding_chars_format.setBackground(QColor("#f0f0f0"))  # Light gray background

        # Error format
        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor(HL7SoupColors.ERROR_BACKGROUND))

        # Warning format
        self.warning_format = QTextCharFormat()
        self.warning_format.setBackground(QColor(HL7SoupColors.WARNING_BACKGROUND))
    
    def highlightBlock(self, text: str):
        """Highlight a block of text.
        
        Args:
            text: Text to highlight
        """
        if not text.strip():
            return
        
        # Detect HL7 separators
        separators = self._detect_separators(text)
        
        # Highlight segment name (first 3 characters)
        if len(text) >= 3:
            self.setFormat(0, 3, self.segment_format)
        
        # Special handling for MSH segment
        if text.startswith('MSH'):
            self._highlight_msh_segment(text, separators)
        else:
            self._highlight_regular_segment(text, separators)
    
    def _detect_separators(self, text: str) -> HL7Separators:
        """Detect HL7 separators from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            HL7Separators object
        """
        if text.startswith('MSH') and len(text) >= 8:
            return HL7Separators.from_msh_segment(text)
        else:
            return HL7Separators()  # Default separators
    
    def _highlight_msh_segment(self, text: str, separators: HL7Separators):
        """Highlight MSH segment with special handling.
        
        Args:
            text: MSH segment text
            separators: HL7 separators
        """
        if len(text) < 4:
            return
        
        # Highlight field separator after MSH
        if len(text) > 3:
            self.setFormat(3, 1, self.field_separator_format)
        
        # Highlight encoding characters
        if len(text) >= 8:
            self.setFormat(4, 4, self.encoding_chars_format)
        
        # Highlight remaining field separators
        start_pos = 8
        for i, char in enumerate(text[start_pos:], start_pos):
            if char == separators.field:
                self.setFormat(i, 1, self.field_separator_format)
            elif char == separators.component:
                self.setFormat(i, 1, self.component_separator_format)
            elif char == separators.repetition:
                self.setFormat(i, 1, self.repetition_separator_format)
            elif char == separators.subcomponent:
                self.setFormat(i, 1, self.subcomponent_separator_format)
            elif char == separators.escape:
                self.setFormat(i, 1, self.escape_format)
    
    def _highlight_regular_segment(self, text: str, separators: HL7Separators):
        """Highlight regular segment.
        
        Args:
            text: Segment text
            separators: HL7 separators
        """
        # Highlight separators
        for i, char in enumerate(text):
            if char == separators.field:
                self.setFormat(i, 1, self.field_separator_format)
            elif char == separators.component:
                self.setFormat(i, 1, self.component_separator_format)
            elif char == separators.repetition:
                self.setFormat(i, 1, self.repetition_separator_format)
            elif char == separators.subcomponent:
                self.setFormat(i, 1, self.subcomponent_separator_format)
            elif char == separators.escape:
                self.setFormat(i, 1, self.escape_format)


class LineNumberArea(QWidget):
    """Line number area for the HL7 editor."""
    
    def __init__(self, editor):
        """Initialize the line number area.
        
        Args:
            editor: Parent HL7 editor
        """
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self) -> QSize:
        """Return the size hint for the line number area."""
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        """Paint the line numbers."""
        self.editor.line_number_area_paint_event(event)


class HL7TextEditor(QPlainTextEdit):
    """Enhanced text editor for HL7 messages with syntax highlighting and line numbers."""
    
    # Signals
    segment_clicked = pyqtSignal(str, int)  # segment_name, line_number
    field_clicked = pyqtSignal(str, int, int)  # segment_name, line_number, field_number
    content_changed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the HL7 text editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Editor properties
        self.hl7_message: Optional[HL7Message] = None
        self.show_line_numbers = True
        self.highlight_current_line = True
        
        # Set up the editor
        self._setup_editor()
        self._setup_syntax_highlighting()
        self._setup_line_numbers()
        self._connect_signals()
        
        # Validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_content)
        
        self.logger.debug("HL7 text editor initialized")
    
    def _setup_editor(self):
        """Set up the basic editor properties with HL7 Soup styling."""
        # Font - use Courier New like HL7 Soup
        font = QFont("Courier New", 10)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab settings
        self.setTabStopDistance(40)

        # Line wrap
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Accept drops
        self.setAcceptDrops(True)

        # Apply HL7 Soup editor styling
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {HL7SoupColors.PANEL_BACKGROUND};
                border: 2px inset {HL7SoupColors.BORDER_INSET};
                selection-background-color: {HL7SoupColors.SELECTION_BACKGROUND};
                selection-color: {HL7SoupColors.SELECTION_TEXT};
                font-family: "Courier New", "Consolas", monospace;
                font-size: 10px;
                line-height: 1.1;
                color: {HL7SoupColors.TEXT_NORMAL};
            }}
            QPlainTextEdit:focus {{
                border: 2px inset {HL7SoupColors.BORDER_FOCUS};
            }}
        """)

        # Set property for styling
        self.setProperty("hl7Editor", True)
    
    def _setup_syntax_highlighting(self):
        """Set up syntax highlighting."""
        self.highlighter = HL7SyntaxHighlighter(self.document())
    
    def _setup_line_numbers(self):
        """Set up line number area."""
        self.line_number_area = LineNumberArea(self)
        
        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line_func)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line_func()
    
    def _connect_signals(self):
        """Connect editor signals."""
        self.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self):
        """Handle text changes."""
        self.content_changed.emit()
        
        # Start validation timer
        self.validation_timer.start(1000)  # Validate after 1 second of inactivity
    
    def _validate_content(self):
        """Validate the current content."""
        # This would trigger validation of the HL7 content
        # For now, just emit the signal
        pass
    
    def line_number_area_width(self) -> int:
        """Calculate the width needed for line numbers."""
        if not self.show_line_numbers:
            return 0
        
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def update_line_number_area_width(self, new_block_count: int):
        """Update the line number area width."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect: QRect, dy: int):
        """Update the line number area."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
    
    def line_number_area_paint_event(self, event):
        """Paint the line number area."""
        if not self.show_line_numbers:
            return
        
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(
                    0, int(top), self.line_number_area.width(), self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
    
    def highlight_current_line_func(self):
        """Highlight the current line."""
        if not self.highlight_current_line:
            return
        
        extra_selections = []
        
        if not self.isReadOnly():
            from PyQt6.QtWidgets import QTextEdit
            selection = QTextEdit.ExtraSelection()
            
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for hyperlink detection."""
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            self._handle_click_at_cursor(cursor)
        
        super().mousePressEvent(event)
    
    def _handle_click_at_cursor(self, cursor: QTextCursor):
        """Handle click at cursor position for hyperlink detection."""
        # Get the current line
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()
        line_number = cursor.blockNumber() + 1
        
        # Detect segment name
        if len(line_text) >= 3:
            segment_name = line_text[:3]
            self.segment_clicked.emit(segment_name, line_number)
        
        # Detect field position (simplified)
        # This would be enhanced to detect exact field positions
        field_number = self._detect_field_at_position(cursor)
        if field_number > 0:
            segment_name = line_text[:3] if len(line_text) >= 3 else ""
            self.field_clicked.emit(segment_name, line_number, field_number)
    
    def _detect_field_at_position(self, cursor: QTextCursor) -> int:
        """Detect field number at cursor position."""
        # Get the line and cursor position within the line
        line_cursor = QTextCursor(cursor)
        line_cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        line_start = line_cursor.position()
        cursor_pos = cursor.position() - line_start
        
        # Get the line text
        line_cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = line_cursor.selectedText()
        
        # Count field separators before cursor position
        field_count = 1  # Start with field 1
        for i in range(min(cursor_pos, len(line_text))):
            if line_text[i] == '|':
                field_count += 1
        
        return field_count
    
    def set_hl7_message(self, message: HL7Message):
        """Set the HL7 message for this editor.

        Args:
            message: HL7 message to display
        """
        self.hl7_message = message
        self.setPlainText(str(message))

    def get_hl7_content(self) -> str:
        """Get the current HL7 content.

        Returns:
            Current text content
        """
        return self.toPlainText()
