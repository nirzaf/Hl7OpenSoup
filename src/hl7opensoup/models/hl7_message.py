"""
HL7 Message data models for HL7 OpenSoup.

This module contains data models for representing HL7 messages, segments,
fields, components, and subcomponents with validation and parsing capabilities.
"""

import re
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HL7Version(Enum):
    """Supported HL7 versions."""
    V2_1 = "2.1"
    V2_2 = "2.2"
    V2_3 = "2.3"
    V2_3_1 = "2.3.1"
    V2_4 = "2.4"
    V2_5 = "2.5"
    V2_5_1 = "2.5.1"
    V2_6 = "2.6"
    V2_7 = "2.7"
    V2_7_1 = "2.7.1"
    V2_8 = "2.8"
    V2_8_1 = "2.8.1"
    V2_8_2 = "2.8.2"
    V2_9 = "2.9"


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Represents a validation result."""
    level: ValidationLevel
    message: str
    location: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    segment_name: Optional[str] = None
    field_number: Optional[int] = None
    component_number: Optional[int] = None
    subcomponent_number: Optional[int] = None


@dataclass
class HL7Separators:
    """HL7 field separators."""
    field: str = "|"
    component: str = "^"
    repetition: str = "~"
    escape: str = "\\"
    subcomponent: str = "&"
    
    @classmethod
    def from_msh_segment(cls, msh_segment: str) -> 'HL7Separators':
        """Extract separators from MSH segment.
        
        Args:
            msh_segment: MSH segment string
            
        Returns:
            HL7Separators instance
        """
        if len(msh_segment) < 8:
            return cls()  # Return defaults
        
        # MSH|^~\&|...
        # Position 3: field separator (|)
        # Position 4: component separator (^)
        # Position 5: repetition separator (~)
        # Position 6: escape character (\)
        # Position 7: subcomponent separator (&)
        
        field_sep = msh_segment[3] if len(msh_segment) > 3 else "|"
        encoding_chars = msh_segment[4:8] if len(msh_segment) >= 8 else "^~\\&"
        
        return cls(
            field=field_sep,
            component=encoding_chars[0] if len(encoding_chars) > 0 else "^",
            repetition=encoding_chars[1] if len(encoding_chars) > 1 else "~",
            escape=encoding_chars[2] if len(encoding_chars) > 2 else "\\",
            subcomponent=encoding_chars[3] if len(encoding_chars) > 3 else "&"
        )


@dataclass
class HL7Subcomponent:
    """Represents an HL7 subcomponent."""
    value: str = ""
    position: int = 0
    
    def __str__(self) -> str:
        return self.value
    
    def is_empty(self) -> bool:
        """Check if subcomponent is empty."""
        return not self.value.strip()


@dataclass
class HL7Component:
    """Represents an HL7 component."""
    subcomponents: List[HL7Subcomponent] = field(default_factory=list)
    position: int = 0
    
    def __str__(self) -> str:
        return "&".join(str(sub) for sub in self.subcomponents)
    
    def get_subcomponent(self, index: int) -> Optional[HL7Subcomponent]:
        """Get subcomponent by index."""
        if 0 <= index < len(self.subcomponents):
            return self.subcomponents[index]
        return None
    
    def set_subcomponent(self, index: int, value: str) -> None:
        """Set subcomponent value by index."""
        # Extend list if necessary
        while len(self.subcomponents) <= index:
            self.subcomponents.append(HL7Subcomponent("", len(self.subcomponents)))
        
        self.subcomponents[index].value = value
    
    def is_empty(self) -> bool:
        """Check if component is empty."""
        return all(sub.is_empty() for sub in self.subcomponents)


@dataclass
class HL7Field:
    """Represents an HL7 field."""
    components: List[HL7Component] = field(default_factory=list)
    repetitions: List[List[HL7Component]] = field(default_factory=list)
    position: int = 0
    name: str = ""
    data_type: str = ""
    required: bool = False
    max_length: Optional[int] = None
    
    def __str__(self) -> str:
        if self.repetitions:
            # Handle repetitions
            rep_strings = []
            for rep in self.repetitions:
                rep_strings.append("^".join(str(comp) for comp in rep))
            return "~".join(rep_strings)
        else:
            return "^".join(str(comp) for comp in self.components)
    
    def get_component(self, index: int) -> Optional[HL7Component]:
        """Get component by index."""
        if 0 <= index < len(self.components):
            return self.components[index]
        return None
    
    def set_component(self, index: int, value: str) -> None:
        """Set component value by index."""
        # Extend list if necessary
        while len(self.components) <= index:
            self.components.append(HL7Component([], len(self.components)))
        
        # Parse the value into subcomponents
        subcomp_values = value.split("&")
        self.components[index].subcomponents = [
            HL7Subcomponent(val, i) for i, val in enumerate(subcomp_values)
        ]
    
    def get_value(self) -> str:
        """Get the first component's first subcomponent value."""
        if self.components and self.components[0].subcomponents:
            return self.components[0].subcomponents[0].value
        return ""
    
    def set_value(self, value: str) -> None:
        """Set the first component's first subcomponent value."""
        if not self.components:
            self.components.append(HL7Component([], 0))
        
        if not self.components[0].subcomponents:
            self.components[0].subcomponents.append(HL7Subcomponent("", 0))
        
        self.components[0].subcomponents[0].value = value
    
    def is_empty(self) -> bool:
        """Check if field is empty."""
        return all(comp.is_empty() for comp in self.components)


@dataclass
class HL7Segment:
    """Represents an HL7 segment."""
    name: str = ""
    fields: List[HL7Field] = field(default_factory=list)
    raw_content: str = ""
    line_number: int = 0
    required: bool = False
    max_repetitions: int = 1
    
    def __str__(self) -> str:
        if self.raw_content:
            return self.raw_content
        
        field_strings = [self.name]
        for field in self.fields:
            field_strings.append(str(field))
        
        return "|".join(field_strings)
    
    def get_field(self, index: int) -> Optional[HL7Field]:
        """Get field by index (1-based)."""
        if 1 <= index <= len(self.fields):
            return self.fields[index - 1]
        return None
    
    def set_field(self, index: int, value: str) -> None:
        """Set field value by index (1-based)."""
        # Extend list if necessary
        while len(self.fields) < index:
            self.fields.append(HL7Field([], [], len(self.fields) + 1))
        
        field = self.fields[index - 1]
        field.set_value(value)
    
    def get_field_value(self, index: int) -> str:
        """Get field value by index (1-based)."""
        field = self.get_field(index)
        return field.get_value() if field else ""
    
    def is_header_segment(self) -> bool:
        """Check if this is a header segment (MSH, FHS, BHS)."""
        return self.name in ["MSH", "FHS", "BHS"]


@dataclass
class HL7Message:
    """Represents a complete HL7 message."""
    segments: List[HL7Segment] = field(default_factory=list)
    separators: HL7Separators = field(default_factory=HL7Separators)
    version: Optional[HL7Version] = None
    message_type: str = ""
    control_id: str = ""
    timestamp: Optional[datetime] = None
    raw_content: str = ""
    validation_results: List[ValidationResult] = field(default_factory=list)
    file_path: Optional[str] = None
    encoding: str = "utf-8"
    
    def __post_init__(self):
        """Initialize message after creation."""
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        if self.raw_content:
            return self.raw_content
        
        segment_strings = []
        for segment in self.segments:
            segment_strings.append(str(segment))
        
        return "\r".join(segment_strings)
    
    def get_segment(self, name: str, index: int = 0) -> Optional[HL7Segment]:
        """Get segment by name and index."""
        found_segments = [seg for seg in self.segments if seg.name == name]
        if 0 <= index < len(found_segments):
            return found_segments[index]
        return None
    
    def get_segments(self, name: str) -> List[HL7Segment]:
        """Get all segments with the given name."""
        return [seg for seg in self.segments if seg.name == name]
    
    def get_msh_segment(self) -> Optional[HL7Segment]:
        """Get the MSH (Message Header) segment."""
        return self.get_segment("MSH")
    
    def get_message_type(self) -> str:
        """Extract message type from MSH segment."""
        msh = self.get_msh_segment()
        if msh:
            # MSH.9 contains message type (full field value)
            field = msh.get_field(9)
            if field:
                return str(field)  # Return full field value with components
            return msh.get_field_value(9)  # Fallback to first component only
        return ""
    
    def get_control_id(self) -> str:
        """Extract control ID from MSH segment."""
        msh = self.get_msh_segment()
        if msh:
            # MSH.10 contains control ID
            return msh.get_field_value(10)
        return ""
    
    def get_version(self) -> Optional[HL7Version]:
        """Extract HL7 version from MSH segment."""
        msh = self.get_msh_segment()
        if msh:
            # MSH.12 contains version
            version_str = msh.get_field_value(12)
            try:
                return HL7Version(version_str)
            except ValueError:
                pass
        return None
    
    def add_validation_result(self, result: ValidationResult) -> None:
        """Add a validation result."""
        self.validation_results.append(result)
    
    def has_errors(self) -> bool:
        """Check if message has validation errors."""
        return any(
            result.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
            for result in self.validation_results
        )
    
    def has_warnings(self) -> bool:
        """Check if message has validation warnings."""
        return any(
            result.level == ValidationLevel.WARNING
            for result in self.validation_results
        )
    
    def clear_validation_results(self) -> None:
        """Clear all validation results."""
        self.validation_results.clear()
    
    def is_valid(self) -> bool:
        """Check if message is valid (no errors or critical issues)."""
        return not self.has_errors()


@dataclass
class HL7MessageCollection:
    """Represents a collection of HL7 messages from a file."""
    messages: List[HL7Message] = field(default_factory=list)
    file_path: Optional[str] = None
    encoding: str = "utf-8"
    last_modified: Optional[datetime] = None
    
    def __len__(self) -> int:
        return len(self.messages)
    
    def __iter__(self):
        return iter(self.messages)
    
    def __getitem__(self, index: int) -> HL7Message:
        return self.messages[index]
    
    def add_message(self, message: HL7Message) -> None:
        """Add a message to the collection."""
        self.messages.append(message)
    
    def remove_message(self, index: int) -> bool:
        """Remove a message by index."""
        if 0 <= index < len(self.messages):
            del self.messages[index]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
    
    def get_message_types(self) -> List[str]:
        """Get unique message types in the collection."""
        types = set()
        for message in self.messages:
            msg_type = message.get_message_type()
            if msg_type:
                types.add(msg_type)
        return sorted(list(types))
    
    def filter_by_type(self, message_type: str) -> List[HL7Message]:
        """Filter messages by type."""
        return [msg for msg in self.messages if msg.get_message_type() == message_type]
    
    def filter_by_content(self, search_term: str, case_sensitive: bool = False) -> List[HL7Message]:
        """Filter messages by content."""
        if not case_sensitive:
            search_term = search_term.lower()
        
        filtered = []
        for message in self.messages:
            content = str(message)
            if not case_sensitive:
                content = content.lower()
            
            if search_term in content:
                filtered.append(message)
        
        return filtered
