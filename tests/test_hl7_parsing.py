"""
Tests for HL7 parsing functionality.

This module contains tests for the HL7 parser, validator, and data models.
"""

import sys
import pytest
from pathlib import Path

# Add src to path for testing
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from hl7opensoup.models.hl7_message import (
    HL7Message, HL7Segment, HL7Field, HL7Component, HL7Subcomponent,
    HL7Separators, HL7Version, ValidationResult, ValidationLevel,
    HL7MessageCollection
)
from hl7opensoup.core.hl7_parser import HL7Parser, HL7ParseError
from hl7opensoup.core.hl7_validator import HL7Validator


# Sample HL7 messages for testing
SAMPLE_ADT_MESSAGE = """MSH|^~\\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|20230101120000||ADT^A01^ADT_A01|12345|P|2.5
EVN||20230101120000|||^SMITH^JOHN
PID|1||123456789^^^MRN^MR||DOE^JANE^MARIE||19800101|F||C|123 MAIN ST^^ANYTOWN^ST^12345||(555)123-4567|(555)987-6543|EN|M|CHR|987654321|||||||||||20230101120000
NK1|1|DOE^JOHN^||123 MAIN ST^^ANYTOWN^ST^12345|(555)123-4567|N
PV1|1|I|ICU^101^1|||123456^DOCTOR^ATTENDING|||SUR||||A|||123456^DOCTOR^ATTENDING|INP|CAT||||||||||||||||||||SF|A|||20230101120000"""

SAMPLE_ORU_MESSAGE = """MSH|^~\\&|LAB|HOSPITAL|EMR|CLINIC|20230101120000||ORU^R01^ORU_R01|67890|P|2.5
PID|1||987654321^^^MRN^MR||SMITH^JOHN^DAVID||19750615|M||W|456 OAK AVE^^SOMEWHERE^CA^90210||(555)555-5555||EN|S|CHR|111223333
OBR|1|ORDER123|RESULT456|CBC^COMPLETE BLOOD COUNT^L|||20230101100000|20230101110000||||||||123456^DOCTOR^ORDERING||||||||F
OBX|1|NM|WBC^WHITE BLOOD COUNT^L||7.5|10*3/uL|4.0-11.0|N|||F
OBX|2|NM|RBC^RED BLOOD COUNT^L||4.2|10*6/uL|4.2-5.4|N|||F
OBX|3|NM|HGB^HEMOGLOBIN^L||13.5|g/dL|12.0-16.0|N|||F"""

INVALID_MESSAGE = """INVALID|SEGMENT|FORMAT
PID|1||123456789^^^MRN^MR||DOE^JANE^MARIE||19800101|F"""


class TestHL7Separators:
    """Test HL7 separators functionality."""
    
    def test_default_separators(self):
        """Test default separator values."""
        separators = HL7Separators()
        assert separators.field == "|"
        assert separators.component == "^"
        assert separators.repetition == "~"
        assert separators.escape == "\\"
        assert separators.subcomponent == "&"
    
    def test_from_msh_segment(self):
        """Test extracting separators from MSH segment."""
        msh = "MSH|^~\\&|SENDING_APP|RECEIVING_APP"
        separators = HL7Separators.from_msh_segment(msh)
        
        assert separators.field == "|"
        assert separators.component == "^"
        assert separators.repetition == "~"
        assert separators.escape == "\\"
        assert separators.subcomponent == "&"
    
    def test_custom_separators(self):
        """Test custom separators."""
        msh = "MSH|#$%@|SENDING_APP|RECEIVING_APP"
        separators = HL7Separators.from_msh_segment(msh)
        
        assert separators.field == "|"
        assert separators.component == "#"
        assert separators.repetition == "$"
        assert separators.escape == "%"
        assert separators.subcomponent == "@"


class TestHL7DataModels:
    """Test HL7 data model classes."""
    
    def test_subcomponent(self):
        """Test HL7Subcomponent."""
        subcomp = HL7Subcomponent("test_value", 0)
        assert str(subcomp) == "test_value"
        assert not subcomp.is_empty()
        
        empty_subcomp = HL7Subcomponent("", 0)
        assert empty_subcomp.is_empty()
    
    def test_component(self):
        """Test HL7Component."""
        comp = HL7Component()
        comp.subcomponents = [
            HL7Subcomponent("value1", 0),
            HL7Subcomponent("value2", 1)
        ]
        
        assert str(comp) == "value1&value2"
        assert comp.get_subcomponent(0).value == "value1"
        assert comp.get_subcomponent(1).value == "value2"
        assert comp.get_subcomponent(2) is None
    
    def test_field(self):
        """Test HL7Field."""
        field = HL7Field()
        field.set_value("test_value")
        
        assert field.get_value() == "test_value"
        assert not field.is_empty()
        
        # Test component setting
        field.set_component(0, "comp1&subcomp1")
        assert field.get_component(0).subcomponents[0].value == "comp1"
        assert field.get_component(0).subcomponents[1].value == "subcomp1"
    
    def test_segment(self):
        """Test HL7Segment."""
        segment = HL7Segment(name="PID")
        segment.set_field(1, "123456789")
        segment.set_field(5, "DOE^JANE")
        
        assert segment.get_field_value(1) == "123456789"
        assert segment.get_field_value(5) == "DOE^JANE"
        assert segment.get_field_value(10) == ""  # Non-existent field
    
    def test_message(self):
        """Test HL7Message."""
        message = HL7Message()
        
        # Add MSH segment
        msh = HL7Segment(name="MSH")
        msh.set_field(9, "ADT^A01")
        msh.set_field(10, "12345")
        msh.set_field(12, "2.5")
        message.segments.append(msh)
        
        # Add PID segment
        pid = HL7Segment(name="PID")
        pid.set_field(3, "123456789")
        message.segments.append(pid)
        
        assert message.get_message_type() == "ADT^A01"
        assert message.get_control_id() == "12345"
        assert message.get_version() == HL7Version.V2_5
        assert len(message.get_segments("PID")) == 1


class TestHL7Parser:
    """Test HL7 parser functionality."""
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = HL7Parser()
        assert parser is not None
    
    def test_parse_basic_message(self):
        """Test parsing a basic HL7 message."""
        parser = HL7Parser()
        message = parser.parse_message(SAMPLE_ADT_MESSAGE)
        
        assert message is not None
        assert len(message.segments) > 0
        assert message.segments[0].name == "MSH"
        assert message.get_message_type() == "ADT^A01^ADT_A01"
        assert message.get_control_id() == "12345"
    
    def test_parse_multiple_messages(self):
        """Test parsing multiple messages."""
        parser = HL7Parser()
        combined_messages = SAMPLE_ADT_MESSAGE + "\n\n" + SAMPLE_ORU_MESSAGE
        messages = parser.parse_messages(combined_messages)
        
        assert len(messages) == 2
        assert messages[0].get_message_type() == "ADT^A01^ADT_A01"
        assert messages[1].get_message_type() == "ORU^R01^ORU_R01"
    
    def test_parse_invalid_message(self):
        """Test parsing invalid message."""
        parser = HL7Parser()
        message = parser.parse_message(INVALID_MESSAGE)
        
        # Should still create a message object with validation errors
        assert message is not None
        assert len(message.validation_results) > 0
    
    def test_encoding_detection(self):
        """Test encoding detection."""
        parser = HL7Parser()
        
        # Test UTF-8
        utf8_data = SAMPLE_ADT_MESSAGE.encode('utf-8')
        encoding = parser.detect_encoding(utf8_data)
        assert encoding in ['utf-8', 'ascii']  # ASCII is subset of UTF-8
        
        # Test with BOM
        utf8_bom_data = b'\xef\xbb\xbf' + SAMPLE_ADT_MESSAGE.encode('utf-8')
        encoding = parser.detect_encoding(utf8_bom_data)
        assert 'utf' in encoding.lower()


class TestHL7Validator:
    """Test HL7 validator functionality."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = HL7Validator()
        assert validator is not None
        assert "MSH" in validator.segment_definitions
        assert "PID" in validator.segment_definitions
    
    def test_validate_valid_message(self):
        """Test validating a valid message."""
        parser = HL7Parser()
        validator = HL7Validator()
        
        message = parser.parse_message(SAMPLE_ADT_MESSAGE)
        results = validator.validate_message(message)
        
        # Should have some validation results (warnings are OK)
        assert isinstance(results, list)
        
        # Check that no critical errors exist
        critical_errors = [r for r in results if r.level == ValidationLevel.ERROR]
        assert len(critical_errors) == 0
    
    def test_validate_invalid_message(self):
        """Test validating an invalid message."""
        parser = HL7Parser()
        validator = HL7Validator()
        
        message = parser.parse_message(INVALID_MESSAGE)
        results = validator.validate_message(message)
        
        # Should have validation errors
        assert len(results) > 0
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
    
    def test_segment_definitions(self):
        """Test segment definitions."""
        validator = HL7Validator()
        
        # Test MSH segment definition
        msh_def = validator.segment_definitions["MSH"]
        assert msh_def.name == "MSH"
        assert msh_def.required is True
        assert 9 in msh_def.fields  # Message type field
        assert msh_def.fields[9].required is True
        
        # Test PID segment definition
        pid_def = validator.segment_definitions["PID"]
        assert pid_def.name == "PID"
        assert 3 in pid_def.fields  # Patient identifier list
        assert pid_def.fields[3].required is True


class TestHL7MessageCollection:
    """Test HL7 message collection functionality."""
    
    def test_collection_creation(self):
        """Test creating a message collection."""
        collection = HL7MessageCollection()
        assert len(collection) == 0
        assert list(collection) == []
    
    def test_collection_operations(self):
        """Test collection operations."""
        parser = HL7Parser()
        collection = HL7MessageCollection()
        
        # Add messages
        message1 = parser.parse_message(SAMPLE_ADT_MESSAGE)
        message2 = parser.parse_message(SAMPLE_ORU_MESSAGE)
        
        collection.add_message(message1)
        collection.add_message(message2)
        
        assert len(collection) == 2
        assert collection[0] == message1
        assert collection[1] == message2
        
        # Test message types
        types = collection.get_message_types()
        assert "ADT^A01^ADT_A01" in types
        assert "ORU^R01^ORU_R01" in types
        
        # Test filtering
        adt_messages = collection.filter_by_type("ADT^A01^ADT_A01")
        assert len(adt_messages) == 1
        
        # Test content filtering
        jane_messages = collection.filter_by_content("JANE")
        assert len(jane_messages) == 1
        
        # Test removal
        assert collection.remove_message(0) is True
        assert len(collection) == 1
        assert collection.remove_message(5) is False  # Invalid index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
