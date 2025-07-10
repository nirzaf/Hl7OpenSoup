"""
MongoDB Configuration Dialog for HL7 OpenSoup.

This module provides a dialog for configuring MongoDB connection settings
and managing database operations.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QGroupBox, QDialogButtonBox,
    QTextEdit, QProgressBar, QMessageBox, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont

from hl7opensoup.database.mongodb_connector import MongoDBConnector, MongoDBConfig
from hl7opensoup.ui.hl7_soup_style import HL7SoupColors, get_panel_title_style


class ConnectionTestWorker(QThread):
    """Worker thread for testing MongoDB connection."""
    
    test_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, config: MongoDBConfig):
        """Initialize connection test worker.
        
        Args:
            config: MongoDB configuration to test
        """
        super().__init__()
        self.config = config
    
    def run(self):
        """Run the connection test."""
        connector = MongoDBConnector(self.config)
        success, message = connector.test_connection()
        self.test_completed.emit(success, message)


class MongoDBDialog(QDialog):
    """Dialog for MongoDB configuration and management."""
    
    def __init__(self, parent=None):
        """Initialize the MongoDB dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = MongoDBConfig()
        self.connector: Optional[MongoDBConnector] = None
        self.test_worker: Optional[ConnectionTestWorker] = None
        
        self.setWindowTitle("MongoDB Configuration - HL7 OpenSoup")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._connect_signals()
        self._load_config()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Connection tab
        connection_tab = self._create_connection_tab()
        self.tab_widget.addTab(connection_tab, "Connection")
        
        # Management tab
        management_tab = self._create_management_tab()
        self.tab_widget.addTab(management_tab, "Management")
        
        # Statistics tab
        statistics_tab = self._create_statistics_tab()
        self.tab_widget.addTab(statistics_tab, "Statistics")
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_config)
        layout.addWidget(button_box)
        
        self.apply_button = button_box.button(QDialogButtonBox.StandardButton.Apply)
    
    def _create_connection_tab(self) -> QWidget:
        """Create connection configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection settings group
        conn_group = QGroupBox("Connection Settings")
        conn_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        conn_layout = QGridLayout(conn_group)
        
        # Host
        conn_layout.addWidget(QLabel("Host:"), 0, 0)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        conn_layout.addWidget(self.host_input, 0, 1)
        
        # Port
        conn_layout.addWidget(QLabel("Port:"), 0, 2)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(27017)
        conn_layout.addWidget(self.port_input, 0, 3)
        
        # Database
        conn_layout.addWidget(QLabel("Database:"), 1, 0)
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("hl7opensoup")
        conn_layout.addWidget(self.database_input, 1, 1)
        
        # Collection
        conn_layout.addWidget(QLabel("Collection:"), 1, 2)
        self.collection_input = QLineEdit()
        self.collection_input.setPlaceholderText("messages")
        conn_layout.addWidget(self.collection_input, 1, 3)
        
        layout.addWidget(conn_group)
        
        # Authentication group
        auth_group = QGroupBox("Authentication")
        auth_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        auth_layout = QGridLayout(auth_group)
        
        # Username
        auth_layout.addWidget(QLabel("Username:"), 0, 0)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Optional")
        auth_layout.addWidget(self.username_input, 0, 1)
        
        # Password
        auth_layout.addWidget(QLabel("Password:"), 0, 2)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Optional")
        auth_layout.addWidget(self.password_input, 0, 3)
        
        # Auth source
        auth_layout.addWidget(QLabel("Auth Source:"), 1, 0)
        self.auth_source_input = QLineEdit()
        self.auth_source_input.setPlaceholderText("admin")
        auth_layout.addWidget(self.auth_source_input, 1, 1)
        
        layout.addWidget(auth_group)
        
        # SSL group
        ssl_group = QGroupBox("SSL/TLS")
        ssl_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        ssl_layout = QVBoxLayout(ssl_group)
        
        self.ssl_checkbox = QCheckBox("Enable SSL/TLS")
        ssl_layout.addWidget(self.ssl_checkbox)
        
        layout.addWidget(ssl_group)
        
        # Connection test
        test_group = QGroupBox("Connection Test")
        test_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        test_layout = QVBoxLayout(test_group)
        
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        test_button_layout.addWidget(self.test_button)
        test_button_layout.addStretch()
        test_layout.addLayout(test_button_layout)
        
        self.test_result = QTextEdit()
        self.test_result.setMaximumHeight(100)
        self.test_result.setReadOnly(True)
        test_layout.addWidget(self.test_result)
        
        layout.addWidget(test_group)
        
        layout.addStretch()
        return tab
    
    def _create_management_tab(self) -> QWidget:
        """Create database management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status = QLabel("Not connected")
        self.connection_status.setStyleSheet(f"color: {HL7SoupColors.TEXT_DISABLED};")
        status_layout.addWidget(self.connection_status)
        
        connect_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect_database)
        connect_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self._disconnect_database)
        self.disconnect_button.setEnabled(False)
        connect_layout.addWidget(self.disconnect_button)
        
        connect_layout.addStretch()
        status_layout.addLayout(connect_layout)
        
        layout.addWidget(status_group)
        
        # Database operations
        ops_group = QGroupBox("Database Operations")
        ops_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        ops_layout = QVBoxLayout(ops_group)
        
        # Backup/Restore
        backup_layout = QHBoxLayout()
        
        self.backup_button = QPushButton("Backup Messages")
        self.backup_button.clicked.connect(self._backup_messages)
        self.backup_button.setEnabled(False)
        backup_layout.addWidget(self.backup_button)
        
        self.restore_button = QPushButton("Restore Messages")
        self.restore_button.clicked.connect(self._restore_messages)
        self.restore_button.setEnabled(False)
        backup_layout.addWidget(self.restore_button)
        
        backup_layout.addStretch()
        ops_layout.addLayout(backup_layout)
        
        # Clear data
        clear_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear All Messages")
        self.clear_button.clicked.connect(self._clear_messages)
        self.clear_button.setEnabled(False)
        self.clear_button.setStyleSheet("QPushButton { color: red; }")
        clear_layout.addWidget(self.clear_button)
        
        clear_layout.addStretch()
        ops_layout.addLayout(clear_layout)
        
        layout.addWidget(ops_group)
        
        # Operation log
        log_group = QGroupBox("Operation Log")
        log_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {HL7SoupColors.TEXT_TITLE}; }}")
        log_layout = QVBoxLayout(log_group)
        
        self.operation_log = QTextEdit()
        self.operation_log.setReadOnly(True)
        self.operation_log.setMaximumHeight(150)
        log_layout.addWidget(self.operation_log)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        return tab
    
    def _create_statistics_tab(self) -> QWidget:
        """Create statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_stats_button = QPushButton("Refresh Statistics")
        self.refresh_stats_button.clicked.connect(self._refresh_statistics)
        self.refresh_stats_button.setEnabled(False)
        refresh_layout.addWidget(self.refresh_stats_button)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Statistics display
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        layout.addWidget(self.statistics_text)
        
        return tab
    
    def _connect_signals(self):
        """Connect UI signals."""
        # Update config when inputs change
        self.host_input.textChanged.connect(self._update_config)
        self.port_input.valueChanged.connect(self._update_config)
        self.database_input.textChanged.connect(self._update_config)
        self.collection_input.textChanged.connect(self._update_config)
        self.username_input.textChanged.connect(self._update_config)
        self.password_input.textChanged.connect(self._update_config)
        self.auth_source_input.textChanged.connect(self._update_config)
        self.ssl_checkbox.toggled.connect(self._update_config)
    
    def _load_config(self):
        """Load configuration into UI."""
        self.host_input.setText(self.config.host)
        self.port_input.setValue(self.config.port)
        self.database_input.setText(self.config.database)
        self.collection_input.setText(self.config.collection)
        self.username_input.setText(self.config.username or "")
        self.password_input.setText(self.config.password or "")
        self.auth_source_input.setText(self.config.auth_source)
        self.ssl_checkbox.setChecked(self.config.ssl)
    
    def _update_config(self):
        """Update configuration from UI."""
        self.config.host = self.host_input.text() or "localhost"
        self.config.port = self.port_input.value()
        self.config.database = self.database_input.text() or "hl7opensoup"
        self.config.collection = self.collection_input.text() or "messages"
        self.config.username = self.username_input.text() or None
        self.config.password = self.password_input.text() or None
        self.config.auth_source = self.auth_source_input.text() or "admin"
        self.config.ssl = self.ssl_checkbox.isChecked()
    
    def _test_connection(self):
        """Test MongoDB connection."""
        self._update_config()
        
        self.test_button.setEnabled(False)
        self.test_result.setText("Testing connection...")
        
        # Start test worker
        self.test_worker = ConnectionTestWorker(self.config)
        self.test_worker.test_completed.connect(self._on_test_completed)
        self.test_worker.start()
    
    def _on_test_completed(self, success: bool, message: str):
        """Handle connection test completion."""
        self.test_button.setEnabled(True)
        
        if success:
            self.test_result.setStyleSheet(f"color: {HL7SoupColors.TEXT_NORMAL};")
            self.test_result.setText(f"✓ {message}")
        else:
            self.test_result.setStyleSheet("color: red;")
            self.test_result.setText(f"✗ {message}")
    
    def _apply_config(self):
        """Apply configuration changes."""
        self._update_config()
        self._log_operation("Configuration updated")
    
    def _connect_database(self):
        """Connect to MongoDB."""
        self._update_config()
        
        if not self.connector:
            self.connector = MongoDBConnector(self.config)
        
        if self.connector.connect():
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet(f"color: green;")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.backup_button.setEnabled(True)
            self.restore_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.refresh_stats_button.setEnabled(True)
            self._log_operation("Connected to MongoDB")
            self._refresh_statistics()
        else:
            self.connection_status.setText("Connection failed")
            self.connection_status.setStyleSheet("color: red;")
            self._log_operation("Failed to connect to MongoDB")
    
    def _disconnect_database(self):
        """Disconnect from MongoDB."""
        if self.connector:
            self.connector.disconnect()
        
        self.connection_status.setText("Not connected")
        self.connection_status.setStyleSheet(f"color: {HL7SoupColors.TEXT_DISABLED};")
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.backup_button.setEnabled(False)
        self.restore_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.refresh_stats_button.setEnabled(False)
        self._log_operation("Disconnected from MongoDB")
    
    def _backup_messages(self):
        """Backup messages to file."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Backup Messages", "hl7_backup.json", "JSON Files (*.json)"
        )
        
        if file_path and self.connector:
            if self.connector.backup_to_file(file_path):
                self._log_operation(f"Messages backed up to {file_path}")
                QMessageBox.information(self, "Backup", "Messages backed up successfully")
            else:
                self._log_operation(f"Failed to backup messages to {file_path}")
                QMessageBox.critical(self, "Backup", "Failed to backup messages")
    
    def _restore_messages(self):
        """Restore messages from file."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restore Messages", "", "JSON Files (*.json)"
        )
        
        if file_path and self.connector:
            reply = QMessageBox.question(
                self, "Restore", 
                "This will add messages from the backup file to the database. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.connector.restore_from_file(file_path):
                    self._log_operation(f"Messages restored from {file_path}")
                    QMessageBox.information(self, "Restore", "Messages restored successfully")
                    self._refresh_statistics()
                else:
                    self._log_operation(f"Failed to restore messages from {file_path}")
                    QMessageBox.critical(self, "Restore", "Failed to restore messages")
    
    def _clear_messages(self):
        """Clear all messages from database."""
        reply = QMessageBox.warning(
            self, "Clear Messages",
            "This will permanently delete ALL messages from the database. This action cannot be undone.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.connector and self.connector.collection:
                result = self.connector.collection.delete_many({})
                self._log_operation(f"Cleared {result.deleted_count} messages from database")
                QMessageBox.information(self, "Clear", f"Deleted {result.deleted_count} messages")
                self._refresh_statistics()
    
    def _refresh_statistics(self):
        """Refresh database statistics."""
        if not self.connector or not self.connector.is_connected():
            self.statistics_text.setText("Not connected to database")
            return
        
        stats = self.connector.get_statistics()
        
        stats_text = f"""Database Statistics:

Total Messages: {stats.get('total_messages', 0)}
Recent Messages (24h): {stats.get('recent_messages', 0)}

Message Types:
"""
        
        for msg_type, count in stats.get('message_types', {}).items():
            stats_text += f"  {msg_type}: {count}\n"
        
        stats_text += "\nValidation Status:\n"
        for status, count in stats.get('validation_status', {}).items():
            stats_text += f"  {status}: {count}\n"
        
        self.statistics_text.setText(stats_text)
    
    def _log_operation(self, message: str):
        """Log operation to the operation log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.operation_log.append(f"[{timestamp}] {message}")
    
    def get_config(self) -> MongoDBConfig:
        """Get the current configuration.
        
        Returns:
            MongoDB configuration
        """
        self._update_config()
        return self.config
