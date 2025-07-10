"""
HL7 Validation Engine for HL7 OpenSoup.

This module provides comprehensive HL7 message validation capabilities
including standard schema validation and custom rule support.
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass

from hl7opensoup.models.hl7_message import (
    HL7Message, HL7Segment, HL7Field, ValidationResult, ValidationLevel, HL7Version
)


@dataclass
class FieldDefinition:
    """Definition of an HL7 field."""
    position: int
    name: str
    data_type: str
    required: bool = False
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    repeatable: bool = False
    table_id: Optional[str] = None
    description: str = ""


@dataclass
class SegmentDefinition:
    """Definition of an HL7 segment."""
    name: str
    description: str
    fields: Dict[int, FieldDefinition]
    required: bool = False
    repeatable: bool = False
    max_repetitions: Optional[int] = None


@dataclass
class MessageDefinition:
    """Definition of an HL7 message type."""
    message_type: str
    event_type: str
    description: str
    segments: List[str]  # Ordered list of segment names
    required_segments: Set[str]
    version: HL7Version


class HL7Validator:
    """HL7 message validator with schema support."""
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = logging.getLogger(__name__)
        self.segment_definitions: Dict[str, SegmentDefinition] = {}
        self.message_definitions: Dict[str, MessageDefinition] = {}
        self.data_type_patterns: Dict[str, str] = {}
        self.table_values: Dict[str, Set[str]] = {}
        
        # Load default schemas
        self._load_default_schemas()
    
    def _load_default_schemas(self):
        """Load default HL7 schemas."""
        # Define common data type patterns
        self.data_type_patterns = {
            'ST': r'^.{0,200}$',  # String
            'TX': r'^.*$',        # Text
            'FT': r'^.*$',        # Formatted text
            'NM': r'^[+-]?\d*\.?\d*$',  # Numeric
            'SI': r'^[+-]?\d{1,4}$',    # Sequence ID
            'ID': r'^[A-Z0-9]*$',       # Coded value
            'IS': r'^[A-Z0-9]*$',       # Coded value from table
            'DT': r'^\d{8}$',           # Date (YYYYMMDD)
            'TM': r'^\d{2,6}$',         # Time (HHMMSS)
            'TS': r'^\d{8,14}$',        # Timestamp
            'HD': r'^.*$',              # Hierarchic designator
            'EI': r'^.*$',              # Entity identifier
            'CX': r'^.*$',              # Extended composite ID
            'XPN': r'^.*$',             # Extended person name
            'XAD': r'^.*$',             # Extended address
            'XTN': r'^.*$',             # Extended telecommunication
            'CE': r'^.*$',              # Coded element
            'CF': r'^.*$',              # Coded element with formatted values
            'CNE': r'^.*$',             # Coded with no exceptions
            'CWE': r'^.*$',             # Coded with exceptions
        }
        
        # Define common segments
        self._define_msh_segment()
        self._define_pid_segment()
        self._define_pv1_segment()
        self._define_obx_segment()
        self._define_common_segments()
    
    def _define_msh_segment(self):
        """Define MSH (Message Header) segment."""
        fields = {
            1: FieldDefinition(1, "Field Separator", "ST", True, 1, 1),
            2: FieldDefinition(2, "Encoding Characters", "ST", True, 4, 4),
            3: FieldDefinition(3, "Sending Application", "HD", False, 227),
            4: FieldDefinition(4, "Sending Facility", "HD", False, 227),
            5: FieldDefinition(5, "Receiving Application", "HD", False, 227),
            6: FieldDefinition(6, "Receiving Facility", "HD", False, 227),
            7: FieldDefinition(7, "Date/Time of Message", "TS", False, 26),
            8: FieldDefinition(8, "Security", "ST", False, 40),
            9: FieldDefinition(9, "Message Type", "MSG", True, 15),
            10: FieldDefinition(10, "Message Control ID", "ST", True, 20),
            11: FieldDefinition(11, "Processing ID", "PT", True, 3),
            12: FieldDefinition(12, "Version ID", "VID", True, 60),
            13: FieldDefinition(13, "Sequence Number", "NM", False, 15),
            14: FieldDefinition(14, "Continuation Pointer", "ST", False, 180),
            15: FieldDefinition(15, "Accept Acknowledgment Type", "ID", False, 2),
            16: FieldDefinition(16, "Application Acknowledgment Type", "ID", False, 2),
            17: FieldDefinition(17, "Country Code", "ID", False, 3),
            18: FieldDefinition(18, "Character Set", "ID", False, 16, repeatable=True),
            19: FieldDefinition(19, "Principal Language of Message", "CE", False, 250),
        }
        
        self.segment_definitions["MSH"] = SegmentDefinition(
            name="MSH",
            description="Message Header",
            fields=fields,
            required=True
        )
    
    def _define_pid_segment(self):
        """Define PID (Patient Identification) segment."""
        fields = {
            1: FieldDefinition(1, "Set ID - PID", "SI", False, 4),
            2: FieldDefinition(2, "Patient ID", "CX", False, 20),
            3: FieldDefinition(3, "Patient Identifier List", "CX", True, 250, repeatable=True),
            4: FieldDefinition(4, "Alternate Patient ID - PID", "CX", False, 20, repeatable=True),
            5: FieldDefinition(5, "Patient Name", "XPN", True, 250, repeatable=True),
            6: FieldDefinition(6, "Mother's Maiden Name", "XPN", False, 250, repeatable=True),
            7: FieldDefinition(7, "Date/Time of Birth", "TS", False, 26),
            8: FieldDefinition(8, "Administrative Sex", "IS", False, 1, table_id="0001"),
            9: FieldDefinition(9, "Patient Alias", "XPN", False, 250, repeatable=True),
            10: FieldDefinition(10, "Race", "CE", False, 250, repeatable=True),
            11: FieldDefinition(11, "Patient Address", "XAD", False, 250, repeatable=True),
            12: FieldDefinition(12, "County Code", "IS", False, 4),
            13: FieldDefinition(13, "Phone Number - Home", "XTN", False, 250, repeatable=True),
            14: FieldDefinition(14, "Phone Number - Business", "XTN", False, 250, repeatable=True),
            15: FieldDefinition(15, "Primary Language", "CE", False, 250),
            16: FieldDefinition(16, "Marital Status", "CE", False, 250),
            17: FieldDefinition(17, "Religion", "CE", False, 250),
            18: FieldDefinition(18, "Patient Account Number", "CX", False, 250),
            19: FieldDefinition(19, "SSN Number - Patient", "ST", False, 16),
            20: FieldDefinition(20, "Driver's License Number - Patient", "DLN", False, 25),
        }
        
        self.segment_definitions["PID"] = SegmentDefinition(
            name="PID",
            description="Patient Identification",
            fields=fields,
            required=True
        )
    
    def _define_pv1_segment(self):
        """Define PV1 (Patient Visit) segment."""
        fields = {
            1: FieldDefinition(1, "Set ID - PV1", "SI", False, 4),
            2: FieldDefinition(2, "Patient Class", "IS", True, 1, table_id="0004"),
            3: FieldDefinition(3, "Assigned Patient Location", "PL", False, 80),
            4: FieldDefinition(4, "Admission Type", "IS", False, 2, table_id="0007"),
            5: FieldDefinition(5, "Preadmit Number", "CX", False, 250),
            6: FieldDefinition(6, "Prior Patient Location", "PL", False, 80),
            7: FieldDefinition(7, "Attending Doctor", "XCN", False, 250, repeatable=True),
            8: FieldDefinition(8, "Referring Doctor", "XCN", False, 250, repeatable=True),
            9: FieldDefinition(9, "Consulting Doctor", "XCN", False, 250, repeatable=True),
            10: FieldDefinition(10, "Hospital Service", "IS", False, 3, table_id="0069"),
        }
        
        self.segment_definitions["PV1"] = SegmentDefinition(
            name="PV1",
            description="Patient Visit",
            fields=fields
        )
    
    def _define_obx_segment(self):
        """Define OBX (Observation/Result) segment."""
        fields = {
            1: FieldDefinition(1, "Set ID - OBX", "SI", False, 4),
            2: FieldDefinition(2, "Value Type", "ID", False, 2, table_id="0125"),
            3: FieldDefinition(3, "Observation Identifier", "CE", True, 250),
            4: FieldDefinition(4, "Observation Sub-ID", "ST", False, 20),
            5: FieldDefinition(5, "Observation Value", "Varies", False, 99999, repeatable=True),
            6: FieldDefinition(6, "Units", "CE", False, 250),
            7: FieldDefinition(7, "References Range", "ST", False, 60),
            8: FieldDefinition(8, "Abnormal Flags", "IS", False, 5, repeatable=True, table_id="0078"),
            9: FieldDefinition(9, "Probability", "NM", False, 5),
            10: FieldDefinition(10, "Nature of Abnormal Test", "ID", False, 2, repeatable=True, table_id="0080"),
            11: FieldDefinition(11, "Observation Result Status", "ID", True, 1, table_id="0085"),
        }
        
        self.segment_definitions["OBX"] = SegmentDefinition(
            name="OBX",
            description="Observation/Result",
            fields=fields,
            repeatable=True
        )
    
    def _define_common_segments(self):
        """Define other common segments."""
        # EVN - Event Type
        self.segment_definitions["EVN"] = SegmentDefinition(
            name="EVN",
            description="Event Type",
            fields={
                1: FieldDefinition(1, "Event Type Code", "ID", False, 3),
                2: FieldDefinition(2, "Recorded Date/Time", "TS", True, 26),
                3: FieldDefinition(3, "Date/Time Planned Event", "TS", False, 26),
                4: FieldDefinition(4, "Event Reason Code", "IS", False, 3),
                5: FieldDefinition(5, "Operator ID", "XCN", False, 250, repeatable=True),
                6: FieldDefinition(6, "Event Occurred", "TS", False, 26),
            }
        )
        
        # NK1 - Next of Kin
        self.segment_definitions["NK1"] = SegmentDefinition(
            name="NK1",
            description="Next of Kin/Associated Parties",
            fields={
                1: FieldDefinition(1, "Set ID - NK1", "SI", True, 4),
                2: FieldDefinition(2, "Name", "XPN", False, 250, repeatable=True),
                3: FieldDefinition(3, "Relationship", "CE", False, 250),
                4: FieldDefinition(4, "Address", "XAD", False, 250, repeatable=True),
                5: FieldDefinition(5, "Phone Number", "XTN", False, 250, repeatable=True),
            },
            repeatable=True
        )
    
    def validate_message(self, message: HL7Message) -> List[ValidationResult]:
        """Validate an HL7 message.
        
        Args:
            message: HL7 message to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        # Clear existing validation results
        message.clear_validation_results()
        
        # Basic structure validation
        results.extend(self._validate_structure(message))
        
        # Segment validation
        results.extend(self._validate_segments(message))
        
        # Field validation
        results.extend(self._validate_fields(message))
        
        # Data type validation
        results.extend(self._validate_data_types(message))
        
        # Table validation
        results.extend(self._validate_tables(message))
        
        # Add results to message
        for result in results:
            message.add_validation_result(result)
        
        return results
    
    def _validate_structure(self, message: HL7Message) -> List[ValidationResult]:
        """Validate basic message structure."""
        results = []
        
        # Check if message has segments
        if not message.segments:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Message has no segments",
                location="message"
            ))
            return results
        
        # Check if first segment is MSH
        first_segment = message.segments[0]
        if first_segment.name != "MSH":
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"First segment must be MSH, found {first_segment.name}",
                location="segment",
                segment_name=first_segment.name,
                line_number=first_segment.line_number
            ))
        
        # Check for required segments based on message type
        msg_type = message.get_message_type()
        if msg_type in self.message_definitions:
            msg_def = self.message_definitions[msg_type]
            segment_names = [seg.name for seg in message.segments]
            
            for required_seg in msg_def.required_segments:
                if required_seg not in segment_names:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Required segment {required_seg} is missing",
                        location="message"
                    ))
        
        return results
    
    def _validate_segments(self, message: HL7Message) -> List[ValidationResult]:
        """Validate individual segments."""
        results = []
        
        for segment in message.segments:
            if segment.name in self.segment_definitions:
                seg_def = self.segment_definitions[segment.name]
                
                # Check field count
                expected_fields = len(seg_def.fields)
                actual_fields = len(segment.fields)
                
                if actual_fields > expected_fields:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Segment {segment.name} has {actual_fields} fields, expected {expected_fields}",
                        location="segment",
                        segment_name=segment.name,
                        line_number=segment.line_number
                    ))
        
        return results
    
    def _validate_fields(self, message: HL7Message) -> List[ValidationResult]:
        """Validate fields within segments."""
        results = []

        for segment in message.segments:
            if segment.name in self.segment_definitions:
                seg_def = self.segment_definitions[segment.name]

                # Check required fields
                for pos, field_def in seg_def.fields.items():
                    if field_def.required:
                        field = segment.get_field(pos)

                        # Special handling for MSH segment fields 1 and 2
                        if segment.name == "MSH" and pos in [1, 2]:
                            # These fields are always present in a valid MSH segment
                            if not field:
                                results.append(ValidationResult(
                                    level=ValidationLevel.ERROR,
                                    message=f"Required field {field_def.name} is missing",
                                    location="field",
                                    segment_name=segment.name,
                                    field_number=pos,
                                    line_number=segment.line_number
                                ))
                        else:
                            # Normal field validation
                            if not field or field.is_empty():
                                results.append(ValidationResult(
                                    level=ValidationLevel.ERROR,
                                    message=f"Required field {field_def.name} is missing or empty",
                                    location="field",
                                    segment_name=segment.name,
                                    field_number=pos,
                                    line_number=segment.line_number
                                ))

                # Check field lengths
                for i, field in enumerate(segment.fields, 1):
                    if i in seg_def.fields:
                        field_def = seg_def.fields[i]
                        field_value = field.get_value()

                        if field_def.max_length and len(field_value) > field_def.max_length:
                            results.append(ValidationResult(
                                level=ValidationLevel.WARNING,
                                message=f"Field {field_def.name} exceeds maximum length of {field_def.max_length}",
                                location="field",
                                segment_name=segment.name,
                                field_number=i,
                                line_number=segment.line_number
                            ))

                        if field_def.min_length and len(field_value) < field_def.min_length:
                            results.append(ValidationResult(
                                level=ValidationLevel.WARNING,
                                message=f"Field {field_def.name} is below minimum length of {field_def.min_length}",
                                location="field",
                                segment_name=segment.name,
                                field_number=i,
                                line_number=segment.line_number
                            ))

        return results
    
    def _validate_data_types(self, message: HL7Message) -> List[ValidationResult]:
        """Validate field data types."""
        results = []
        
        for segment in message.segments:
            if segment.name in self.segment_definitions:
                seg_def = self.segment_definitions[segment.name]
                
                for i, field in enumerate(segment.fields, 1):
                    if i in seg_def.fields:
                        field_def = seg_def.fields[i]
                        field_value = field.get_value()
                        
                        if field_value and field_def.data_type in self.data_type_patterns:
                            pattern = self.data_type_patterns[field_def.data_type]
                            if not re.match(pattern, field_value):
                                results.append(ValidationResult(
                                    level=ValidationLevel.WARNING,
                                    message=f"Field {field_def.name} does not match data type {field_def.data_type}",
                                    location="field",
                                    segment_name=segment.name,
                                    field_number=i,
                                    line_number=segment.line_number
                                ))
        
        return results
    
    def _validate_tables(self, message: HL7Message) -> List[ValidationResult]:
        """Validate table values."""
        results = []
        
        # Table validation would be implemented here
        # This would check against HL7 tables for coded values
        
        return results
    
    def load_custom_schema(self, schema_path: str) -> bool:
        """Load a custom validation schema.
        
        Args:
            schema_path: Path to the schema file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            # Parse and load schema data
            # Implementation would depend on schema format
            
            self.logger.info(f"Loaded custom schema from {schema_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load schema {schema_path}: {e}")
            return False
