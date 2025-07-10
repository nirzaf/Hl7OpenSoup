"""
File utilities for HL7 OpenSoup.

This module provides utility functions for file operations, validation,
and encoding detection specific to HL7 files.
"""

import os
import re
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import chardet


class HL7FileValidator:
    """Validator for HL7 files."""
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = logging.getLogger(__name__)
    
    def is_valid_hl7_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """Check if a file appears to be a valid HL7 file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check file exists and is readable
            if not os.path.exists(file_path):
                issues.append("File does not exist")
                return False, issues
            
            if not os.path.isfile(file_path):
                issues.append("Path is not a file")
                return False, issues
            
            if not os.access(file_path, os.R_OK):
                issues.append("File is not readable")
                return False, issues
            
            # Check file size (warn if very large)
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                issues.append("File is empty")
                return False, issues
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                issues.append("File is very large (>100MB), may take time to load")
            
            # Read a sample of the file to check content
            with open(file_path, 'rb') as f:
                sample = f.read(8192)  # Read first 8KB
            
            # Detect encoding
            encoding_result = chardet.detect(sample)
            encoding = encoding_result.get('encoding', 'utf-8')
            confidence = encoding_result.get('confidence', 0)
            
            if confidence < 0.7:
                issues.append(f"Uncertain encoding detection (confidence: {confidence:.2f})")
            
            # Decode sample
            try:
                sample_text = sample.decode(encoding, errors='replace')
            except Exception as e:
                issues.append(f"Failed to decode file: {e}")
                return False, issues
            
            # Check for HL7 patterns
            has_msh = bool(re.search(r'^MSH\|', sample_text, re.MULTILINE))
            has_segments = bool(re.search(r'^[A-Z]{2,3}\|', sample_text, re.MULTILINE))
            
            if not has_msh and not has_segments:
                issues.append("No HL7 segments found in file")
                return False, issues
            
            if not has_msh:
                issues.append("No MSH (Message Header) segments found")
            
            # Check for common HL7 separators
            if '|' not in sample_text:
                issues.append("No field separators (|) found")
            
            # Check line endings
            if '\r\n' in sample_text:
                self.logger.debug("File uses Windows line endings (CRLF)")
            elif '\n' in sample_text:
                self.logger.debug("File uses Unix line endings (LF)")
            elif '\r' in sample_text:
                self.logger.debug("File uses Mac line endings (CR)")
                issues.append("File uses old Mac line endings (CR only)")
            
            return True, issues
            
        except Exception as e:
            issues.append(f"Error validating file: {e}")
            return False, issues
    
    def detect_hl7_version(self, file_path: str) -> Optional[str]:
        """Detect HL7 version from file content.
        
        Args:
            file_path: Path to the HL7 file
            
        Returns:
            Detected HL7 version or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Read first few lines to find MSH segment
                for _ in range(10):  # Check first 10 lines
                    line = f.readline()
                    if not line:
                        break
                    
                    if line.startswith('MSH|'):
                        # MSH.12 contains version
                        fields = line.split('|')
                        if len(fields) >= 12:
                            version = fields[11].strip()
                            if version:
                                return version
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting HL7 version: {e}")
            return None
    
    def count_messages(self, file_path: str) -> int:
        """Count the number of HL7 messages in a file.
        
        Args:
            file_path: Path to the HL7 file
            
        Returns:
            Number of messages found
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Count MSH segments (each represents a message)
            msh_count = len(re.findall(r'^MSH\|', content, re.MULTILINE))
            
            # Also count FHS segments (file header segments)
            fhs_count = len(re.findall(r'^FHS\|', content, re.MULTILINE))
            
            # Return the higher count (some files might not have MSH for each message)
            return max(msh_count, fhs_count)
            
        except Exception as e:
            self.logger.error(f"Error counting messages: {e}")
            return 0


class HL7FileManager:
    """Manager for HL7 file operations."""
    
    def __init__(self):
        """Initialize the file manager."""
        self.logger = logging.getLogger(__name__)
        self.validator = HL7FileValidator()
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported extensions
        """
        return ['.hl7', '.txt', '.msg', '.dat']
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file extension is supported.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if supported, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.get_supported_extensions()
    
    def backup_file(self, file_path: str) -> Optional[str]:
        """Create a backup of a file before modifying.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            backup_path = f"{file_path}.backup"
            
            # If backup already exists, create numbered backup
            counter = 1
            while os.path.exists(backup_path):
                backup_path = f"{file_path}.backup.{counter}"
                counter += 1
            
            # Copy file
            import shutil
            shutil.copy2(file_path, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def validate_before_save(self, content: str) -> Tuple[bool, List[str]]:
        """Validate content before saving.
        
        Args:
            content: Content to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if not content.strip():
            issues.append("Content is empty")
            return False, issues
        
        # Check for basic HL7 structure
        lines = content.split('\n')
        has_segments = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like an HL7 segment
            if re.match(r'^[A-Z]{2,3}\|', line):
                has_segments = True
                break
        
        if not has_segments:
            issues.append("No valid HL7 segments found in content")
            return False, issues
        
        return True, issues
    
    def safe_write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Safely write content to file with backup.
        
        Args:
            file_path: Path to write to
            content: Content to write
            encoding: File encoding
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate content first
            is_valid, issues = self.validate_before_save(content)
            if not is_valid:
                self.logger.error(f"Content validation failed: {issues}")
                return False
            
            # Create backup if file exists
            if os.path.exists(file_path):
                backup_path = self.backup_file(file_path)
                if not backup_path:
                    self.logger.warning("Failed to create backup, proceeding anyway")
            
            # Write to temporary file first
            temp_path = f"{file_path}.tmp"
            
            with open(temp_path, 'w', encoding=encoding, newline='') as f:
                f.write(content)
            
            # Move temporary file to final location
            import shutil
            shutil.move(temp_path, file_path)
            
            self.logger.info(f"Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            
            # Clean up temporary file if it exists
            temp_path = f"{file_path}.tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """Get information about an HL7 file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'path': file_path,
            'exists': False,
            'size': 0,
            'encoding': None,
            'is_valid_hl7': False,
            'message_count': 0,
            'hl7_version': None,
            'issues': []
        }
        
        try:
            if os.path.exists(file_path):
                info['exists'] = True
                info['size'] = os.path.getsize(file_path)
                
                # Validate file
                is_valid, issues = self.validator.is_valid_hl7_file(file_path)
                info['is_valid_hl7'] = is_valid
                info['issues'] = issues
                
                if is_valid:
                    info['message_count'] = self.validator.count_messages(file_path)
                    info['hl7_version'] = self.validator.detect_hl7_version(file_path)
                
                # Detect encoding
                with open(file_path, 'rb') as f:
                    sample = f.read(8192)
                    encoding_result = chardet.detect(sample)
                    info['encoding'] = encoding_result.get('encoding', 'utf-8')
        
        except Exception as e:
            info['issues'].append(f"Error getting file info: {e}")
        
        return info
