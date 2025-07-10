"""
Export Dialog for HL7 OpenSoup.

This module provides a dialog for exporting HL7 messages to various formats
with customizable options.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QGroupBox, QLineEdit, QFileDialog,
    QDialogButtonBox, QProgressBar, QTextEdit, QSpinBox, QRadioButton,
    QButtonGroup, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont

from hl7opensoup.models.hl7_message import HL7Message, HL7MessageCollection
from hl7opensoup.core.hl7_exporter import HL7Exporter, HL7ExportFormat
from hl7opensoup.ui.hl7_soup_style import HL7SoupColors, get_panel_title_style


class ExportWorker(QThread):
    """Worker thread for export operations."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, exporter: HL7Exporter, messages: List[HL7Message], 
                 file_path: str, export_format: str, options: Dict[str, Any]):
        """Initialize export worker.
        
        Args:
            exporter: HL7Exporter instance
            messages: Messages to export
            file_path: Output file path
            export_format: Export format
            options: Export options
        """
        super().__init__()
        self.exporter = exporter
        self.messages = messages
        self.file_path = file_path
        self.export_format = export_format
        self.options = options
    
    def run(self):
        """Run the export operation."""
        try:
            self.status_updated.emit("Starting export...")
            self.progress_updated.emit(10)
            
            self.status_updated.emit("Preparing data...")
            self.progress_updated.emit(30)
            
            self.status_updated.emit("Exporting messages...")
            self.progress_updated.emit(50)
            
            success = self.exporter.export_messages(
                self.messages, self.file_path, self.export_format, self.options
            )
            
            self.progress_updated.emit(100)
            
            if success:
                self.status_updated.emit("Export completed successfully")
                self.export_completed.emit(True, f"Successfully exported {len(self.messages)} messages")
            else:
                self.status_updated.emit("Export failed")
                self.export_completed.emit(False, "Export operation failed")
                
        except Exception as e:
            self.status_updated.emit(f"Export error: {e}")
            self.export_completed.emit(False, f"Export failed: {e}")


class ExportDialog(QDialog):
    """Dialog for exporting HL7 messages."""
    
    def __init__(self, collection: HL7MessageCollection, parent=None):
        """Initialize the export dialog.
        
        Args:
            collection: HL7 message collection to export
            parent: Parent widget
        """
        super().__init__(parent)
        self.collection = collection
        self.exporter = HL7Exporter()
        self.logger = logging.getLogger(__name__)
        self.export_worker: Optional[ExportWorker] = None
        
        self.setWindowTitle("Export HL7 Messages - HL7 OpenSoup")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._connect_signals()
        self._update_format_options()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Export format selection
        format_group = self._create_format_group()
        layout.addWidget(format_group)
        
        # Message selection
        selection_group = self._create_selection_group()
        layout.addWidget(selection_group)
        
        # Export options
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Output file selection
        output_group = self._create_output_group()
        layout.addWidget(output_group)
        
        # Progress section
        progress_group = self._create_progress_group()
        layout.addWidget(progress_group)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        button_box.accepted.connect(self._start_export)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.export_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
    
    def _create_format_group(self) -> QGroupBox:
        """Create export format selection group."""
        group = QGroupBox("Export Format")
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        
        layout = QVBoxLayout(group)
        
        self.format_combo = QComboBox()
        formats = self.exporter.get_supported_formats()
        for format_key, description in formats.items():
            self.format_combo.addItem(description, format_key)
        
        layout.addWidget(self.format_combo)
        
        return group
    
    def _create_selection_group(self) -> QGroupBox:
        """Create message selection group."""
        group = QGroupBox("Message Selection")
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        
        layout = QVBoxLayout(group)
        
        # Selection options
        self.selection_group = QButtonGroup()
        
        self.all_messages_radio = QRadioButton("Export all messages")
        self.all_messages_radio.setChecked(True)
        self.selection_group.addButton(self.all_messages_radio)
        layout.addWidget(self.all_messages_radio)
        
        self.current_message_radio = QRadioButton("Export current message only")
        self.selection_group.addButton(self.current_message_radio)
        layout.addWidget(self.current_message_radio)
        
        self.range_radio = QRadioButton("Export message range:")
        self.selection_group.addButton(self.range_radio)
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(self.range_radio)
        
        range_layout.addWidget(QLabel("From:"))
        self.range_from = QSpinBox()
        self.range_from.setMinimum(1)
        self.range_from.setMaximum(len(self.collection.messages))
        self.range_from.setValue(1)
        self.range_from.setEnabled(False)
        range_layout.addWidget(self.range_from)
        
        range_layout.addWidget(QLabel("To:"))
        self.range_to = QSpinBox()
        self.range_to.setMinimum(1)
        self.range_to.setMaximum(len(self.collection.messages))
        self.range_to.setValue(len(self.collection.messages))
        self.range_to.setEnabled(False)
        range_layout.addWidget(self.range_to)
        
        range_layout.addStretch()
        layout.addLayout(range_layout)
        
        # Message count info
        self.message_count_label = QLabel(f"Total messages: {len(self.collection.messages)}")
        self.message_count_label.setStyleSheet(f"color: {HL7SoupColors.TEXT_DISABLED}; font-style: italic;")
        layout.addWidget(self.message_count_label)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create export options group."""
        group = QGroupBox("Export Options")
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        
        layout = QVBoxLayout(group)
        
        # Common options
        self.include_headers_check = QCheckBox("Include headers and metadata")
        self.include_headers_check.setChecked(True)
        layout.addWidget(self.include_headers_check)
        
        self.include_validation_check = QCheckBox("Include validation results")
        self.include_validation_check.setChecked(True)
        layout.addWidget(self.include_validation_check)
        
        # Format-specific options
        self.format_options_frame = QFrame()
        self.format_options_layout = QVBoxLayout(self.format_options_frame)
        layout.addWidget(self.format_options_frame)
        
        return group
    
    def _create_output_group(self) -> QGroupBox:
        """Create output file selection group."""
        group = QGroupBox("Output File")
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        
        layout = QHBoxLayout(group)
        
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output file...")
        layout.addWidget(self.output_path)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_output_file)
        layout.addWidget(self.browse_button)
        
        return group
    
    def _create_progress_group(self) -> QGroupBox:
        """Create progress group."""
        group = QGroupBox("Export Progress")
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        group.setVisible(False)
        
        layout = QVBoxLayout(group)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to export")
        self.status_label.setStyleSheet(f"color: {HL7SoupColors.TEXT_DISABLED};")
        layout.addWidget(self.status_label)
        
        self.progress_group = group
        return group
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.format_combo.currentTextChanged.connect(self._update_format_options)
        self.range_radio.toggled.connect(self._on_range_selection_changed)
        
        # Update output file extension when format changes
        self.format_combo.currentTextChanged.connect(self._update_output_extension)
    
    def _update_format_options(self):
        """Update format-specific options."""
        # Clear existing options
        for i in reversed(range(self.format_options_layout.count())):
            self.format_options_layout.itemAt(i).widget().setParent(None)
        
        format_key = self.format_combo.currentData()
        
        if format_key == HL7ExportFormat.CSV:
            self.detailed_csv_check = QCheckBox("Detailed export (all segments and fields)")
            self.detailed_csv_check.setChecked(True)
            self.format_options_layout.addWidget(self.detailed_csv_check)
            
        elif format_key == HL7ExportFormat.JSON:
            self.pretty_json_check = QCheckBox("Pretty print JSON")
            self.pretty_json_check.setChecked(True)
            self.format_options_layout.addWidget(self.pretty_json_check)
            
            self.include_raw_check = QCheckBox("Include raw HL7 content")
            self.format_options_layout.addWidget(self.include_raw_check)
            
        elif format_key == HL7ExportFormat.TEXT:
            self.text_separator_label = QLabel("Message separator:")
            self.format_options_layout.addWidget(self.text_separator_label)
            
            self.text_separator = QLineEdit("\\n" + "="*80 + "\\n")
            self.format_options_layout.addWidget(self.text_separator)
    
    def _on_range_selection_changed(self, checked: bool):
        """Handle range selection changes."""
        self.range_from.setEnabled(checked)
        self.range_to.setEnabled(checked)
    
    def _update_output_extension(self):
        """Update output file extension based on format."""
        current_path = self.output_path.text()
        if current_path:
            path = Path(current_path)
            format_key = self.format_combo.currentData()
            
            # Map format to extension
            extensions = {
                HL7ExportFormat.CSV: ".csv",
                HL7ExportFormat.EXCEL: ".xlsx",
                HL7ExportFormat.JSON: ".json",
                HL7ExportFormat.XML: ".xml",
                HL7ExportFormat.HTML: ".html",
                HL7ExportFormat.TEXT: ".txt",
                HL7ExportFormat.PIPE_DELIMITED: ".txt"
            }
            
            new_extension = extensions.get(format_key, ".txt")
            new_path = path.with_suffix(new_extension)
            self.output_path.setText(str(new_path))
    
    def _browse_output_file(self):
        """Browse for output file."""
        format_key = self.format_combo.currentData()
        format_desc = self.format_combo.currentText()
        
        # Get file extension
        extensions = {
            HL7ExportFormat.CSV: "csv",
            HL7ExportFormat.EXCEL: "xlsx",
            HL7ExportFormat.JSON: "json",
            HL7ExportFormat.XML: "xml",
            HL7ExportFormat.HTML: "html",
            HL7ExportFormat.TEXT: "txt",
            HL7ExportFormat.PIPE_DELIMITED: "txt"
        }
        
        ext = extensions.get(format_key, "txt")
        filter_str = f"{format_desc} (*.{ext});;All Files (*)"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export HL7 Messages", f"hl7_export.{ext}", filter_str
        )
        
        if file_path:
            self.output_path.setText(file_path)
    
    def _get_selected_messages(self) -> List[HL7Message]:
        """Get selected messages for export."""
        if self.all_messages_radio.isChecked():
            return list(self.collection.messages)
        elif self.current_message_radio.isChecked():
            # Return current message (would need to be passed from main window)
            return [self.collection.messages[0]] if self.collection.messages else []
        elif self.range_radio.isChecked():
            start = self.range_from.value() - 1
            end = self.range_to.value()
            return list(self.collection.messages[start:end])
        else:
            return []
    
    def _get_export_options(self) -> Dict[str, Any]:
        """Get export options from UI."""
        options = {
            'include_headers': self.include_headers_check.isChecked(),
            'include_validation': self.include_validation_check.isChecked()
        }
        
        format_key = self.format_combo.currentData()
        
        if format_key == HL7ExportFormat.CSV:
            if hasattr(self, 'detailed_csv_check'):
                options['include_segments'] = self.detailed_csv_check.isChecked()
                options['include_fields'] = self.detailed_csv_check.isChecked()
                
        elif format_key == HL7ExportFormat.JSON:
            if hasattr(self, 'pretty_json_check'):
                options['pretty_print'] = self.pretty_json_check.isChecked()
            if hasattr(self, 'include_raw_check'):
                options['include_raw'] = self.include_raw_check.isChecked()
                
        elif format_key == HL7ExportFormat.TEXT:
            if hasattr(self, 'text_separator'):
                separator = self.text_separator.text()
                # Convert escape sequences
                separator = separator.replace('\\n', '\n').replace('\\t', '\t')
                options['separator'] = separator
        
        return options
    
    def _start_export(self):
        """Start the export process."""
        # Validate inputs
        if not self.output_path.text().strip():
            QMessageBox.warning(self, "Export Error", "Please select an output file.")
            return
        
        messages = self._get_selected_messages()
        if not messages:
            QMessageBox.warning(self, "Export Error", "No messages selected for export.")
            return
        
        # Show progress
        self.progress_group.setVisible(True)
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start export worker
        format_key = self.format_combo.currentData()
        options = self._get_export_options()
        
        self.export_worker = ExportWorker(
            self.exporter, messages, self.output_path.text(), format_key, options
        )
        
        self.export_worker.progress_updated.connect(self.progress_bar.setValue)
        self.export_worker.status_updated.connect(self.status_label.setText)
        self.export_worker.export_completed.connect(self._on_export_completed)
        
        self.export_worker.start()
    
    def _on_export_completed(self, success: bool, message: str):
        """Handle export completion."""
        self.export_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", message)
            self.progress_group.setVisible(False)
