"""
HL7 Parser for HL7 OpenSoup.

This module provides HL7 message parsing functionality using both hl7apy and hl7
libraries for comprehensive parsing and validation capabilities.
"""

import re
import logging
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import chardet

try:
    import hl7apy
    from hl7apy.core import Message as HL7apyMessage, Segment as HL7apySegment
    from hl7apy.parser import parse_message as hl7apy_parse
    from hl7apy.validation import VALIDATION_LEVEL
    HAS_HL7APY = True
except ImportError:
    HAS_HL7APY = False
    logging.warning("hl7apy not available, using basic parsing only")

try:
    import hl7
    HAS_HL7 = True
except ImportError:
    HAS_HL7 = False
    logging.warning("hl7 library not available, using basic parsing only")

from hl7opensoup.models.hl7_message import (
    HL7Message, HL7Segment, HL7Field, HL7Component, HL7Subcomponent,
    HL7Separators, HL7Version, ValidationResult, ValidationLevel,
    HL7MessageCollection
)


class HL7ParseError(Exception):
    """Exception raised when HL7 parsing fails."""
    pass


class HL7Parser:
    """HL7 message parser with support for multiple parsing libraries."""
    
    def __init__(self, use_hl7apy: bool = True, use_hl7: bool = True):
        """Initialize the parser.
        
        Args:
            use_hl7apy: Whether to use hl7apy library for parsing
            use_hl7: Whether to use hl7 library for parsing
        """
        self.logger = logging.getLogger(__name__)
        self.use_hl7apy = use_hl7apy and HAS_HL7APY
        self.use_hl7 = use_hl7 and HAS_HL7
        
        if not (self.use_hl7apy or self.use_hl7):
            self.logger.warning("No HL7 parsing libraries available, using basic parsing")
    
    def detect_encoding(self, data: bytes) -> str:
        """Detect the encoding of HL7 data.
        
        Args:
            data: Raw bytes data
            
        Returns:
            Detected encoding string
        """
        try:
            result = chardet.detect(data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            if confidence > 0.7:
                return encoding
            else:
                return 'utf-8'  # Default fallback
        except Exception:
            return 'utf-8'
    
    def parse_file(self, file_path: str, encoding: Optional[str] = None) -> HL7MessageCollection:
        """Parse HL7 messages from a file.
        
        Args:
            file_path: Path to the HL7 file
            encoding: File encoding (auto-detected if None)
            
        Returns:
            HL7MessageCollection containing parsed messages
            
        Raises:
            HL7ParseError: If parsing fails
        """
        try:
            # Read file with encoding detection
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            if encoding is None:
                encoding = self.detect_encoding(raw_data)
            
            content = raw_data.decode(encoding, errors='replace')
            
            # Parse messages from content
            messages = self.parse_messages(content)
            
            # Create collection
            collection = HL7MessageCollection(
                messages=messages,
                file_path=file_path,
                encoding=encoding,
                last_modified=datetime.now()
            )
            
            self.logger.info(f"Parsed {len(messages)} messages from {file_path}")
            return collection
            
        except Exception as e:
            raise HL7ParseError(f"Failed to parse file {file_path}: {e}")
    
    def parse_messages(self, content: str) -> List[HL7Message]:
        """Parse multiple HL7 messages from content.
        
        Args:
            content: String content containing HL7 messages
            
        Returns:
            List of parsed HL7Message objects
        """
        messages = []
        
        # Split content into individual messages
        # HL7 messages typically start with MSH, FHS, or BHS
        message_pattern = r'(?=^(?:MSH|FHS|BHS)\|)'
        message_strings = re.split(message_pattern, content, flags=re.MULTILINE)
        
        # Remove empty strings
        message_strings = [msg.strip() for msg in message_strings if msg.strip()]
        
        for i, msg_str in enumerate(message_strings):
            try:
                message = self.parse_message(msg_str)
                if message:
                    messages.append(message)
            except Exception as e:
                self.logger.error(f"Failed to parse message {i + 1}: {e}")
                # Create a basic message with error
                error_message = HL7Message(
                    raw_content=msg_str,
                    validation_results=[
                        ValidationResult(
                            level=ValidationLevel.ERROR,
                            message=f"Parse error: {e}",
                            location="message"
                        )
                    ]
                )
                messages.append(error_message)
        
        return messages
    
    def parse_message(self, message_str: str) -> Optional[HL7Message]:
        """Parse a single HL7 message.
        
        Args:
            message_str: String containing a single HL7 message
            
        Returns:
            Parsed HL7Message object or None if parsing fails
        """
        if not message_str.strip():
            return None
        
        # Try parsing with available libraries
        if self.use_hl7apy:
            try:
                return self._parse_with_hl7apy(message_str)
            except Exception as e:
                self.logger.debug(f"hl7apy parsing failed: {e}")
        
        if self.use_hl7:
            try:
                return self._parse_with_hl7(message_str)
            except Exception as e:
                self.logger.debug(f"hl7 library parsing failed: {e}")
        
        # Fallback to basic parsing
        return self._parse_basic(message_str)
    
    def _parse_with_hl7apy(self, message_str: str) -> HL7Message:
        """Parse message using hl7apy library.
        
        Args:
            message_str: HL7 message string
            
        Returns:
            Parsed HL7Message object
        """
        # Parse with hl7apy
        hl7apy_msg = hl7apy_parse(message_str, validation_level=VALIDATION_LEVEL.QUIET)
        
        # Convert to our data model
        message = HL7Message(raw_content=message_str)
        
        # Extract separators from MSH
        if message_str.startswith('MSH'):
            message.separators = HL7Separators.from_msh_segment(message_str.split('\r')[0])
        
        # Convert segments
        for hl7apy_seg in hl7apy_msg.children:
            segment = self._convert_hl7apy_segment(hl7apy_seg, message.separators)
            message.segments.append(segment)
        
        # Extract message metadata
        message.message_type = message.get_message_type()
        message.control_id = message.get_control_id()
        message.version = message.get_version()
        
        return message
    
    def _parse_with_hl7(self, message_str: str) -> HL7Message:
        """Parse message using hl7 library.
        
        Args:
            message_str: HL7 message string
            
        Returns:
            Parsed HL7Message object
        """
        # Parse with hl7 library
        hl7_msg = hl7.parse(message_str)
        
        # Convert to our data model
        message = HL7Message(raw_content=message_str)
        
        # Extract separators
        if message_str.startswith('MSH'):
            message.separators = HL7Separators.from_msh_segment(message_str.split('\r')[0])
        
        # Convert segments
        for i, hl7_seg in enumerate(hl7_msg):
            segment = self._convert_hl7_segment(hl7_seg, message.separators, i)
            message.segments.append(segment)
        
        # Extract message metadata
        message.message_type = message.get_message_type()
        message.control_id = message.get_control_id()
        message.version = message.get_version()
        
        return message
    
    def _parse_basic(self, message_str: str) -> HL7Message:
        """Basic HL7 parsing without external libraries.
        
        Args:
            message_str: HL7 message string
            
        Returns:
            Parsed HL7Message object
        """
        message = HL7Message(raw_content=message_str)
        
        # Split into segments
        segment_strings = message_str.replace('\n', '\r').split('\r')
        segment_strings = [seg.strip() for seg in segment_strings if seg.strip()]
        
        # Extract separators from first segment (should be MSH)
        if segment_strings and segment_strings[0].startswith('MSH'):
            message.separators = HL7Separators.from_msh_segment(segment_strings[0])
        
        # Parse each segment
        for i, seg_str in enumerate(segment_strings):
            segment = self._parse_basic_segment(seg_str, message.separators, i)
            message.segments.append(segment)
        
        # Extract message metadata
        message.message_type = message.get_message_type()
        message.control_id = message.get_control_id()
        message.version = message.get_version()
        
        return message
    
    def _convert_hl7apy_segment(self, hl7apy_seg: 'HL7apySegment', separators: HL7Separators) -> HL7Segment:
        """Convert hl7apy segment to our segment model."""
        segment = HL7Segment(
            name=hl7apy_seg.name,
            raw_content=str(hl7apy_seg)
        )
        
        # Convert fields
        for i, field in enumerate(hl7apy_seg.children):
            hl7_field = HL7Field(position=i + 1)
            
            # Convert components and subcomponents
            if hasattr(field, 'children') and field.children:
                for j, component in enumerate(field.children):
                    hl7_comp = HL7Component(position=j)
                    
                    if hasattr(component, 'children') and component.children:
                        for k, subcomp in enumerate(component.children):
                            hl7_subcomp = HL7Subcomponent(str(subcomp), k)
                            hl7_comp.subcomponents.append(hl7_subcomp)
                    else:
                        hl7_subcomp = HL7Subcomponent(str(component), 0)
                        hl7_comp.subcomponents.append(hl7_subcomp)
                    
                    hl7_field.components.append(hl7_comp)
            else:
                # Simple field
                hl7_comp = HL7Component(position=0)
                hl7_subcomp = HL7Subcomponent(str(field), 0)
                hl7_comp.subcomponents.append(hl7_subcomp)
                hl7_field.components.append(hl7_comp)
            
            segment.fields.append(hl7_field)
        
        return segment
    
    def _convert_hl7_segment(self, hl7_seg, separators: HL7Separators, line_number: int) -> HL7Segment:
        """Convert hl7 library segment to our segment model."""
        segment = HL7Segment(
            name=str(hl7_seg[0]),
            raw_content=str(hl7_seg),
            line_number=line_number
        )
        
        # Convert fields (skip segment name at index 0)
        for i in range(1, len(hl7_seg)):
            field_value = str(hl7_seg[i])
            hl7_field = self._parse_field_value(field_value, separators, i)
            segment.fields.append(hl7_field)
        
        return segment
    
    def _parse_basic_segment(self, segment_str: str, separators: HL7Separators, line_number: int) -> HL7Segment:
        """Parse a segment string using basic parsing."""
        if not segment_str:
            return HL7Segment()

        # Split by field separator
        fields = segment_str.split(separators.field)

        if not fields:
            return HL7Segment()

        segment = HL7Segment(
            name=fields[0],
            raw_content=segment_str,
            line_number=line_number
        )

        # Special handling for MSH segment
        if fields[0] == "MSH":
            # MSH field 1 is the field separator itself
            field1 = HL7Field(position=1)
            field1.set_value(separators.field)
            segment.fields.append(field1)

            # MSH field 2 is the encoding characters
            if len(fields) > 1:
                field2 = HL7Field(position=2)
                field2.set_value(fields[1])
                segment.fields.append(field2)

            # Parse remaining fields starting from index 2 (field 3)
            for i in range(2, len(fields)):
                field_value = fields[i]
                hl7_field = self._parse_field_value(field_value, separators, i + 1)
                segment.fields.append(hl7_field)
        else:
            # Parse fields normally (skip segment name at index 0)
            for i in range(1, len(fields)):
                field_value = fields[i]
                hl7_field = self._parse_field_value(field_value, separators, i)
                segment.fields.append(hl7_field)

        return segment
    
    def _parse_field_value(self, field_value: str, separators: HL7Separators, position: int) -> HL7Field:
        """Parse a field value string."""
        hl7_field = HL7Field(position=position)
        
        # Handle repetitions
        repetitions = field_value.split(separators.repetition)
        
        if len(repetitions) > 1:
            # Multiple repetitions
            for rep in repetitions:
                components = self._parse_components(rep, separators)
                hl7_field.repetitions.append(components)
        else:
            # Single value
            hl7_field.components = self._parse_components(field_value, separators)
        
        return hl7_field
    
    def _parse_components(self, component_str: str, separators: HL7Separators) -> List[HL7Component]:
        """Parse components from a component string."""
        components = []
        component_values = component_str.split(separators.component)
        
        for i, comp_value in enumerate(component_values):
            hl7_comp = HL7Component(position=i)
            
            # Parse subcomponents
            subcomp_values = comp_value.split(separators.subcomponent)
            for j, subcomp_value in enumerate(subcomp_values):
                hl7_subcomp = HL7Subcomponent(subcomp_value, j)
                hl7_comp.subcomponents.append(hl7_subcomp)
            
            components.append(hl7_comp)
        
        return components
