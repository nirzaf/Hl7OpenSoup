"""
HL7 Message Interpreter for HL7 OpenSoup.

This module provides interpretation services for HL7 messages, including
code lookups, field descriptions, and human-readable explanations.
"""

import json
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path

from hl7opensoup.models.hl7_message import HL7Message, HL7Segment, HL7Field


class HL7CodeTable:
    """HL7 code table for value lookups."""
    
    def __init__(self, table_id: str, name: str, codes: Dict[str, str]):
        """Initialize code table.
        
        Args:
            table_id: Table identifier (e.g., "0001")
            name: Table name
            codes: Dictionary of code -> description mappings
        """
        self.table_id = table_id
        self.name = name
        self.codes = codes
    
    def lookup(self, code: str) -> Optional[str]:
        """Look up a code description.
        
        Args:
            code: Code to look up
            
        Returns:
            Description if found, None otherwise
        """
        return self.codes.get(code.upper())


class HL7FieldDefinition:
    """Definition of an HL7 field with interpretation information."""
    
    def __init__(self, segment: str, position: int, name: str, data_type: str,
                 description: str = "", table_id: Optional[str] = None,
                 required: bool = False, repeatable: bool = False):
        """Initialize field definition.
        
        Args:
            segment: Segment name
            position: Field position (1-based)
            name: Field name
            data_type: Data type
            description: Field description
            table_id: Associated table ID for coded values
            required: Whether field is required
            repeatable: Whether field is repeatable
        """
        self.segment = segment
        self.position = position
        self.name = name
        self.data_type = data_type
        self.description = description
        self.table_id = table_id
        self.required = required
        self.repeatable = repeatable


class HL7Interpreter:
    """HL7 message interpreter with code lookup and field descriptions."""
    
    def __init__(self):
        """Initialize the interpreter."""
        self.logger = logging.getLogger(__name__)
        self.code_tables: Dict[str, HL7CodeTable] = {}
        self.field_definitions: Dict[str, Dict[int, HL7FieldDefinition]] = {}
        self.segment_descriptions: Dict[str, str] = {}
        
        # Load default definitions
        self._load_default_definitions()
    
    def _load_default_definitions(self):
        """Load default HL7 definitions and code tables."""
        # Load common code tables
        self._load_common_code_tables()
        
        # Load field definitions
        self._load_field_definitions()
        
        # Load segment descriptions
        self._load_segment_descriptions()
    
    def _load_common_code_tables(self):
        """Load common HL7 code tables."""
        # Table 0001 - Administrative Sex
        self.code_tables["0001"] = HL7CodeTable("0001", "Administrative Sex", {
            "F": "Female",
            "M": "Male",
            "O": "Other",
            "U": "Unknown",
            "A": "Ambiguous",
            "N": "Not applicable"
        })
        
        # Table 0002 - Marital Status
        self.code_tables["0002"] = HL7CodeTable("0002", "Marital Status", {
            "A": "Separated",
            "D": "Divorced",
            "M": "Married",
            "S": "Single",
            "W": "Widowed",
            "C": "Common law",
            "G": "Living together",
            "P": "Domestic partner",
            "R": "Registered domestic partner",
            "E": "Legally separated",
            "N": "Annulled",
            "I": "Interlocutory",
            "B": "Unmarried",
            "U": "Unknown",
            "O": "Other",
            "T": "Unreported"
        })
        
        # Table 0004 - Patient Class
        self.code_tables["0004"] = HL7CodeTable("0004", "Patient Class", {
            "E": "Emergency",
            "I": "Inpatient",
            "O": "Outpatient",
            "P": "Preadmit",
            "R": "Recurring patient",
            "B": "Obstetrics",
            "C": "Commercial account",
            "N": "Not applicable",
            "U": "Unknown"
        })
        
        # Table 0007 - Admission Type
        self.code_tables["0007"] = HL7CodeTable("0007", "Admission Type", {
            "A": "Accident",
            "E": "Emergency",
            "L": "Labor and delivery",
            "R": "Routine",
            "N": "Newborn",
            "U": "Urgent",
            "C": "Elective"
        })
        
        # Table 0078 - Abnormal Flags
        self.code_tables["0078"] = HL7CodeTable("0078", "Abnormal Flags", {
            "L": "Below low normal",
            "H": "Above high normal",
            "LL": "Below lower panic limits",
            "HH": "Above upper panic limits",
            "<": "Below absolute low-off instrument scale",
            ">": "Above absolute high-off instrument scale",
            "N": "Normal",
            "A": "Abnormal",
            "AA": "Very abnormal",
            "null": "No range defined, or normal ranges don't apply",
            "U": "Significant change up",
            "D": "Significant change down",
            "B": "Better",
            "W": "Worse",
            "S": "Susceptible",
            "R": "Resistant",
            "I": "Intermediate",
            "MS": "Moderately susceptible",
            "VS": "Very susceptible"
        })
        
        # Table 0085 - Observation Result Status
        self.code_tables["0085"] = HL7CodeTable("0085", "Observation Result Status", {
            "C": "Record coming over is a correction and thus replaces a final result",
            "D": "Deletes the OBX record",
            "F": "Final results; Can only be changed with a corrected result",
            "I": "Specimen in lab; results pending",
            "N": "Not asked; used to affirmatively document that the observation was not sought when the question could have been asked",
            "O": "Order detail description only (no result)",
            "P": "Preliminary results",
            "R": "Results entered -- not verified",
            "S": "Partial results",
            "U": "Results status change to final without retransmitting results already sent as 'preliminary'",
            "W": "Post original as wrong, e.g., transmitted for wrong patient",
            "X": "Results cannot be obtained for this observation"
        })
        
        # Table 0125 - Value Type
        self.code_tables["0125"] = HL7CodeTable("0125", "Value Type", {
            "AD": "Address",
            "CE": "Coded element",
            "CF": "Coded element with formatted values",
            "CK": "Composite ID with check digit",
            "CN": "Composite ID and name",
            "CP": "Composite price",
            "CX": "Extended composite ID with check digit",
            "DT": "Date",
            "ED": "Encapsulated data",
            "FT": "Formatted text",
            "MO": "Money",
            "NM": "Numeric",
            "PN": "Person name",
            "RP": "Reference pointer",
            "SN": "Structured numeric",
            "ST": "String",
            "TM": "Time",
            "TN": "Telephone number",
            "TS": "Time stamp",
            "TX": "Text",
            "XAD": "Extended address",
            "XCN": "Extended composite ID number and name",
            "XON": "Extended composite name and ID for organizations",
            "XPN": "Extended person name",
            "XTN": "Extended telecommunications number"
        })
    
    def _load_field_definitions(self):
        """Load field definitions for common segments."""
        # MSH - Message Header
        msh_fields = {
            1: HL7FieldDefinition("MSH", 1, "Field Separator", "ST", "Field separator character", required=True),
            2: HL7FieldDefinition("MSH", 2, "Encoding Characters", "ST", "Encoding characters", required=True),
            3: HL7FieldDefinition("MSH", 3, "Sending Application", "HD", "Sending application identifier"),
            4: HL7FieldDefinition("MSH", 4, "Sending Facility", "HD", "Sending facility identifier"),
            5: HL7FieldDefinition("MSH", 5, "Receiving Application", "HD", "Receiving application identifier"),
            6: HL7FieldDefinition("MSH", 6, "Receiving Facility", "HD", "Receiving facility identifier"),
            7: HL7FieldDefinition("MSH", 7, "Date/Time of Message", "TS", "Date and time message was created"),
            8: HL7FieldDefinition("MSH", 8, "Security", "ST", "Security information"),
            9: HL7FieldDefinition("MSH", 9, "Message Type", "MSG", "Message type and trigger event", required=True),
            10: HL7FieldDefinition("MSH", 10, "Message Control ID", "ST", "Unique message identifier", required=True),
            11: HL7FieldDefinition("MSH", 11, "Processing ID", "PT", "Processing ID", required=True),
            12: HL7FieldDefinition("MSH", 12, "Version ID", "VID", "HL7 version", required=True),
            13: HL7FieldDefinition("MSH", 13, "Sequence Number", "NM", "Sequence number"),
            14: HL7FieldDefinition("MSH", 14, "Continuation Pointer", "ST", "Continuation pointer"),
            15: HL7FieldDefinition("MSH", 15, "Accept Acknowledgment Type", "ID", "Accept acknowledgment type"),
            16: HL7FieldDefinition("MSH", 16, "Application Acknowledgment Type", "ID", "Application acknowledgment type"),
            17: HL7FieldDefinition("MSH", 17, "Country Code", "ID", "Country code"),
            18: HL7FieldDefinition("MSH", 18, "Character Set", "ID", "Character set", repeatable=True),
            19: HL7FieldDefinition("MSH", 19, "Principal Language of Message", "CE", "Principal language")
        }
        self.field_definitions["MSH"] = msh_fields
        
        # PID - Patient Identification
        pid_fields = {
            1: HL7FieldDefinition("PID", 1, "Set ID - PID", "SI", "Sequence number for PID segment"),
            2: HL7FieldDefinition("PID", 2, "Patient ID", "CX", "External patient ID"),
            3: HL7FieldDefinition("PID", 3, "Patient Identifier List", "CX", "Internal patient ID", required=True, repeatable=True),
            4: HL7FieldDefinition("PID", 4, "Alternate Patient ID - PID", "CX", "Alternate patient ID", repeatable=True),
            5: HL7FieldDefinition("PID", 5, "Patient Name", "XPN", "Patient's legal name", required=True, repeatable=True),
            6: HL7FieldDefinition("PID", 6, "Mother's Maiden Name", "XPN", "Mother's maiden name", repeatable=True),
            7: HL7FieldDefinition("PID", 7, "Date/Time of Birth", "TS", "Patient's date of birth"),
            8: HL7FieldDefinition("PID", 8, "Administrative Sex", "IS", "Patient's sex", table_id="0001"),
            9: HL7FieldDefinition("PID", 9, "Patient Alias", "XPN", "Patient alias", repeatable=True),
            10: HL7FieldDefinition("PID", 10, "Race", "CE", "Patient's race", repeatable=True),
            11: HL7FieldDefinition("PID", 11, "Patient Address", "XAD", "Patient's address", repeatable=True),
            12: HL7FieldDefinition("PID", 12, "County Code", "IS", "County code"),
            13: HL7FieldDefinition("PID", 13, "Phone Number - Home", "XTN", "Home phone number", repeatable=True),
            14: HL7FieldDefinition("PID", 14, "Phone Number - Business", "XTN", "Business phone number", repeatable=True),
            15: HL7FieldDefinition("PID", 15, "Primary Language", "CE", "Primary language"),
            16: HL7FieldDefinition("PID", 16, "Marital Status", "CE", "Marital status", table_id="0002"),
            17: HL7FieldDefinition("PID", 17, "Religion", "CE", "Religion"),
            18: HL7FieldDefinition("PID", 18, "Patient Account Number", "CX", "Patient account number"),
            19: HL7FieldDefinition("PID", 19, "SSN Number - Patient", "ST", "Social security number"),
            20: HL7FieldDefinition("PID", 20, "Driver's License Number - Patient", "DLN", "Driver's license number")
        }
        self.field_definitions["PID"] = pid_fields
        
        # OBX - Observation/Result
        obx_fields = {
            1: HL7FieldDefinition("OBX", 1, "Set ID - OBX", "SI", "Sequence number for OBX segment"),
            2: HL7FieldDefinition("OBX", 2, "Value Type", "ID", "Data type of observation value", table_id="0125"),
            3: HL7FieldDefinition("OBX", 3, "Observation Identifier", "CE", "Observation identifier", required=True),
            4: HL7FieldDefinition("OBX", 4, "Observation Sub-ID", "ST", "Observation sub-identifier"),
            5: HL7FieldDefinition("OBX", 5, "Observation Value", "Varies", "Observation value", repeatable=True),
            6: HL7FieldDefinition("OBX", 6, "Units", "CE", "Units of measure"),
            7: HL7FieldDefinition("OBX", 7, "References Range", "ST", "Reference range"),
            8: HL7FieldDefinition("OBX", 8, "Abnormal Flags", "IS", "Abnormal flags", table_id="0078", repeatable=True),
            9: HL7FieldDefinition("OBX", 9, "Probability", "NM", "Probability"),
            10: HL7FieldDefinition("OBX", 10, "Nature of Abnormal Test", "ID", "Nature of abnormal test", repeatable=True),
            11: HL7FieldDefinition("OBX", 11, "Observation Result Status", "ID", "Result status", table_id="0085", required=True),
            12: HL7FieldDefinition("OBX", 12, "Effective Date of Reference Range", "TS", "Effective date of reference range"),
            13: HL7FieldDefinition("OBX", 13, "User Defined Access Checks", "ST", "User defined access checks"),
            14: HL7FieldDefinition("OBX", 14, "Date/Time of the Observation", "TS", "Date/time of observation"),
            15: HL7FieldDefinition("OBX", 15, "Producer's ID", "CE", "Producer's identifier")
        }
        self.field_definitions["OBX"] = obx_fields
    
    def _load_segment_descriptions(self):
        """Load segment descriptions."""
        self.segment_descriptions = {
            "MSH": "Message Header - Contains message routing and identification information",
            "EVN": "Event Type - Identifies the trigger event that initiated the message",
            "PID": "Patient Identification - Contains patient demographic information",
            "PD1": "Patient Additional Demographic - Additional patient demographic information",
            "NK1": "Next of Kin/Associated Parties - Information about patient's next of kin",
            "PV1": "Patient Visit - Information about the patient's visit or encounter",
            "PV2": "Patient Visit - Additional Information - Additional visit information",
            "OBR": "Observation Request - Information about the observation/test request",
            "OBX": "Observation/Result - Contains observation values and results",
            "NTE": "Notes and Comments - Free text notes and comments",
            "AL1": "Patient Allergy Information - Information about patient allergies",
            "DG1": "Diagnosis - Diagnosis information",
            "PR1": "Procedures - Procedure information",
            "GT1": "Guarantor - Financial guarantor information",
            "IN1": "Insurance - Primary insurance information",
            "IN2": "Insurance Additional Information - Additional insurance information",
            "IN3": "Insurance Additional Information, Certification - Insurance certification",
            "ACC": "Accident - Accident information",
            "UB1": "UB82 - UB82 billing information",
            "UB2": "UB92 Data - UB92 billing information",
            "MRG": "Merge Patient Information - Patient merge information",
            "PDA": "Patient Death and Autopsy - Death and autopsy information"
        }
    
    def interpret_message(self, message: HL7Message) -> str:
        """Generate interpretation for an HL7 message.
        
        Args:
            message: HL7 message to interpret
            
        Returns:
            HTML formatted interpretation
        """
        interpretation = []
        
        # Message header
        interpretation.append("<h2>Message Interpretation</h2>")
        
        # Basic message info
        msg_type = message.get_message_type()
        control_id = message.get_control_id()
        version = message.get_version()
        
        interpretation.append("<h3>Message Overview</h3>")
        interpretation.append(f"<b>Message Type:</b> {self._interpret_message_type(msg_type)}<br>")
        interpretation.append(f"<b>Control ID:</b> {control_id}<br>")
        interpretation.append(f"<b>Version:</b> {version.value if version else 'Unknown'}<br>")
        interpretation.append(f"<b>Total Segments:</b> {len(message.segments)}<br>")
        
        # Segment summary
        interpretation.append("<h3>Segment Summary</h3>")
        segment_counts = {}
        for segment in message.segments:
            segment_counts[segment.name] = segment_counts.get(segment.name, 0) + 1
        
        for seg_name, count in sorted(segment_counts.items()):
            desc = self.segment_descriptions.get(seg_name, "Unknown segment")
            interpretation.append(f"<b>{seg_name}</b> ({count}): {desc}<br>")
        
        # Validation status
        if message.validation_results:
            interpretation.append("<h3>Validation Results</h3>")
            error_count = len([r for r in message.validation_results if r.level.value == "error"])
            warning_count = len([r for r in message.validation_results if r.level.value == "warning"])
            
            interpretation.append(f"<b>Errors:</b> {error_count}<br>")
            interpretation.append(f"<b>Warnings:</b> {warning_count}<br>")
            
            # Show first few validation results
            for result in message.validation_results[:3]:
                color = "red" if result.level.value == "error" else "orange"
                interpretation.append(f"<span style='color: {color}'>{result.level.value.upper()}: {result.message}</span><br>")
        
        return "".join(interpretation)
    
    def interpret_segment(self, segment: HL7Segment) -> str:
        """Generate interpretation for an HL7 segment.
        
        Args:
            segment: HL7 segment to interpret
            
        Returns:
            HTML formatted interpretation
        """
        interpretation = []
        
        interpretation.append(f"<h3>Segment: {segment.name}</h3>")
        
        # Segment description
        desc = self.segment_descriptions.get(segment.name, "Unknown segment")
        interpretation.append(f"<b>Description:</b> {desc}<br>")
        interpretation.append(f"<b>Fields:</b> {len(segment.fields)}<br>")
        
        # Field interpretations
        if segment.name in self.field_definitions:
            field_defs = self.field_definitions[segment.name]
            interpretation.append("<h4>Field Details</h4>")
            
            for i, field in enumerate(segment.fields, 1):
                if i in field_defs:
                    field_def = field_defs[i]
                    value = field.get_value()
                    
                    interpretation.append(f"<b>{field_def.name} ({i}):</b> ")
                    
                    # Interpret coded values
                    if field_def.table_id and value:
                        table = self.code_tables.get(field_def.table_id)
                        if table:
                            code_desc = table.lookup(value)
                            if code_desc:
                                interpretation.append(f"{value} ({code_desc})")
                            else:
                                interpretation.append(f"{value} (Unknown code)")
                        else:
                            interpretation.append(value)
                    else:
                        interpretation.append(value or "(empty)")
                    
                    interpretation.append("<br>")
        
        return "".join(interpretation)
    
    def interpret_field(self, segment_name: str, field_number: int, field: HL7Field) -> str:
        """Generate interpretation for an HL7 field.
        
        Args:
            segment_name: Name of the segment
            field_number: Field number (1-based)
            field: HL7 field to interpret
            
        Returns:
            HTML formatted interpretation
        """
        interpretation = []
        
        interpretation.append(f"<h4>Field: {segment_name}.{field_number}</h4>")
        
        # Field definition
        if segment_name in self.field_definitions:
            field_defs = self.field_definitions[segment_name]
            if field_number in field_defs:
                field_def = field_defs[field_number]
                
                interpretation.append(f"<b>Name:</b> {field_def.name}<br>")
                interpretation.append(f"<b>Data Type:</b> {field_def.data_type}<br>")
                interpretation.append(f"<b>Description:</b> {field_def.description}<br>")
                interpretation.append(f"<b>Required:</b> {'Yes' if field_def.required else 'No'}<br>")
                interpretation.append(f"<b>Repeatable:</b> {'Yes' if field_def.repeatable else 'No'}<br>")
                
                # Value interpretation
                value = field.get_value()
                interpretation.append(f"<b>Value:</b> {value or '(empty)'}<br>")
                
                # Code lookup
                if field_def.table_id and value:
                    table = self.code_tables.get(field_def.table_id)
                    if table:
                        code_desc = table.lookup(value)
                        if code_desc:
                            interpretation.append(f"<b>Meaning:</b> {code_desc}<br>")
                
                # Component breakdown
                if len(field.components) > 1:
                    interpretation.append("<b>Components:</b><br>")
                    for i, component in enumerate(field.components, 1):
                        comp_value = str(component)
                        if comp_value:
                            interpretation.append(f"&nbsp;&nbsp;{i}: {comp_value}<br>")
        
        return "".join(interpretation)
    
    def _interpret_message_type(self, msg_type: str) -> str:
        """Interpret message type.
        
        Args:
            msg_type: Message type string
            
        Returns:
            Interpreted message type
        """
        if not msg_type:
            return "Unknown"
        
        # Parse message type components
        parts = msg_type.split("^")
        if len(parts) >= 2:
            message_code = parts[0]
            trigger_event = parts[1]
            
            # Common message types
            message_types = {
                "ADT": "Admit, Discharge, Transfer",
                "ORU": "Observation Result",
                "ORM": "Order Message",
                "ORR": "Order Response",
                "SIU": "Scheduling Information",
                "MDM": "Medical Document Management",
                "ACK": "General Acknowledgment",
                "QRY": "Query",
                "DSR": "Display Response"
            }
            
            msg_desc = message_types.get(message_code, message_code)
            return f"{msg_desc} ({msg_type})"
        
        return msg_type
