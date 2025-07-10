# HL7 OpenSoup - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux
- At least 4GB RAM (recommended for large HL7 files)

### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd Hl7OpenSoup
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python src/hl7opensoup/main.py
   ```

   Or use the development script:
   ```bash
   python scripts/run_dev.py
   ```

## 🖥️ Using the Application

### Main Interface

The application replicates the HL7 Soup interface with four main panels:

1. **Messages List Panel** (Left/Right): Lists all loaded HL7 messages
2. **Interpretation Panel** (Top): Human-readable translation of HL7 codes
3. **Main Message Editor** (Center): Raw HL7 message with syntax highlighting
4. **Segment Grid** (Bottom): Tabular view of selected segment fields

### Loading HL7 Messages

1. **File Menu → Open HL7 File** or use Ctrl+O
2. Select your HL7 file (.hl7, .txt, or any text file)
3. Messages will appear in the Messages List panel
4. Click any message to view it in the editor

### Sample Data

The application includes `sample_messages.hl7` with example HL7 messages:
- ADT^A01 (Patient Admission)
- ORU^R01 (Lab Results)

### Key Features

#### Syntax Highlighting
- **Segment IDs**: Bold, colored (MSH, PID, OBR, etc.)
- **Field Separators**: Pipe characters (|)
- **Component Separators**: Caret characters (^)
- **Validation Errors**: Red highlighting for invalid data

#### Real-time Synchronization
- Click any segment in the editor → Segment Grid updates
- Click any field in the grid → Editor highlights the field
- Click any item in Interpretation Panel → Editor navigates to location

#### Search and Filter
- **Ctrl+F**: Search within current message
- **Advanced Search**: Search across all loaded messages
- **Filter Messages**: Filter message list by type, content, etc.

### Exporting Data

1. **File Menu → Export** or use Ctrl+E
2. Choose export format:
   - **JSON**: Structured data format
   - **XML**: Hierarchical markup format
   - **CSV**: Tabular format (configurable fields)
   - **Excel**: Spreadsheet format with formatting
   - **HTML**: Web-viewable format

3. Configure export options (field mappings for CSV)
4. Select output file location

### Validation

- **Automatic Validation**: Messages are validated on load
- **Validation Results**: Shown in status bar and interpretation panel
- **Error Highlighting**: Invalid segments/fields highlighted in red
- **Custom Schemas**: Import custom HL7 schemas for validation

### MongoDB Integration (Optional)

1. **Database Menu → Connect to MongoDB**
2. Enter connection string (mongodb+srv://...)
3. Configure security settings
4. Save/load messages to/from database

## 🧪 Testing the Application

### Run Tests
```bash
# All tests
python -m pytest

# Verbose output
python -m pytest -v

# Specific test file
python -m pytest tests/test_hl7_parsing.py -v
```

### Test Sample Messages
1. Load `sample_messages.hl7`
2. Verify 2 messages are loaded
3. Click each message to view content
4. Try exporting to different formats
5. Test search functionality

## 🔧 Configuration

### Application Settings
- **File Menu → Preferences**
- Configure themes, fonts, validation levels
- Set default export formats and locations
- Configure MongoDB connection settings

### Logging
- Logs are written to application directory
- Debug mode: Set environment variable `HL7_OPENSOUP_LOG_LEVEL=DEBUG`
- Development mode: Use `scripts/run_dev.py`

## 📦 Building Executable

Create a standalone executable for distribution:

```bash
python build_app.py
```

The executable will be created in the `dist/` directory.

## 🆘 Troubleshooting

### Common Issues

1. **PyQt6 Import Error**
   ```bash
   pip install PyQt6
   ```

2. **HL7 Library Missing**
   ```bash
   pip install hl7apy hl7
   ```

3. **Application Won't Start**
   - Check Python version (3.8+)
   - Verify all dependencies installed
   - Run in development mode for detailed error messages

4. **Large File Performance**
   - Files over 10MB may take time to load
   - Use progress bar to monitor loading
   - Consider splitting large files

### Getting Help

1. Check the logs in the application directory
2. Run tests to verify installation: `python -m pytest`
3. Use development mode for detailed error output
4. Review the architectural blueprint for technical details

## 🎯 Next Steps

1. **Load your HL7 files** and explore the interface
2. **Try different export formats** to see the data transformation
3. **Test validation** with both valid and invalid HL7 messages
4. **Explore advanced features** like MongoDB integration
5. **Build an executable** for distribution to other users

The application is designed to be intuitive for anyone familiar with HL7 Soup, providing immediate productivity while offering advanced features for power users.
