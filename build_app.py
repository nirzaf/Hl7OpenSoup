#!/usr/bin/env python3
"""
Build script for HL7 OpenSoup application using PyInstaller.

This script creates a distributable executable following the blueprint specifications.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

def find_pyqt6_plugins():
    """Find PyQt6 plugins directory."""
    try:
        import PyQt6
        pyqt6_path = Path(PyQt6.__file__).parent
        plugins_path = pyqt6_path / "Qt" / "plugins"
        if plugins_path.exists():
            return str(plugins_path)
    except ImportError:
        pass
    return None

def create_spec_file():
    """Create PyInstaller spec file."""
    plugins_path = find_pyqt6_plugins()
    if not plugins_path:
        print("Warning: Could not find PyQt6 plugins directory")
        plugins_path = ""
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Determine the path to PyQt6 plugins
plugins_path = r"{plugins_path}"

block_cipher = None

a = Analysis(
    ['src/hl7opensoup/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        (f'{{plugins_path}}/platforms', 'platforms') if plugins_path else ('', ''),
        (f'{{plugins_path}}/styles', 'styles') if plugins_path else ('', ''),
        (f'{{plugins_path}}/imageformats', 'imageformats') if plugins_path else ('', ''),
        ('sample_messages.hl7', '.'),
        ('src/hl7opensoup/resources', 'resources') if Path('src/hl7opensoup/resources').exists() else ('', ''),
    ],
    hiddenimports=[
        'PyQt6.sip',
        'PyQt6.QtPrintSupport',
        'hl7apy',
        'hl7',
        'pymongo',
        'pandas',
        'openpyxl',
        'lxml',
        'chardet',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HL7OpenSoup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/hl7opensoup/resources/app_icon.ico' if Path('src/hl7opensoup/resources/app_icon.ico').exists() else None,
)
'''
    
    with open('HL7OpenSoup.spec', 'w') as f:
        f.write(spec_content)
    
    print("✓ Created PyInstaller spec file: HL7OpenSoup.spec")

def build_application():
    """Build the application using PyInstaller."""
    try:
        print("Building HL7 OpenSoup application...")
        
        # Create spec file
        create_spec_file()
        
        # Run PyInstaller
        cmd = [sys.executable, '-m', 'PyInstaller', 'HL7OpenSoup.spec', '--clean']
        
        print(f"Running: {{' '.join(cmd)}}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build successful!")
            
            # Check if executable was created
            exe_path = Path('dist/HL7OpenSoup.exe')
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✓ Executable created: {{exe_path}} ({{size_mb:.1f}} MB)")
                return True
            else:
                print("✗ Executable not found in dist directory")
                return False
        else:
            print("✗ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Build error: {{e}}")
        return False

def clean_build():
    """Clean build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['HL7OpenSoup.spec']
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned {{dir_name}}")
    
    for file_name in files_to_clean:
        if Path(file_name).exists():
            Path(file_name).unlink()
            print(f"✓ Cleaned {{file_name}}")

def main():
    """Main build function."""
    print("HL7 OpenSoup Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
        print(f"✓ PyInstaller version: {{PyInstaller.__version__}}")
    except ImportError:
        print("✗ PyInstaller not found. Install with: pip install pyinstaller")
        return 1
    
    # Check if PyQt6 is available
    try:
        import PyQt6
        print(f"✓ PyQt6 available")
    except ImportError:
        print("✗ PyQt6 not found. Install with: pip install PyQt6")
        return 1
    
    # Check if main application file exists
    main_file = Path('src/hl7opensoup/main.py')
    if not main_file.exists():
        print(f"✗ Main application file not found: {{main_file}}")
        return 1
    
    print(f"✓ Main application file found: {{main_file}}")
    
    # Build the application
    if build_application():
        print("\n🎉 Build completed successfully!")
        print("The executable can be found in the 'dist' directory.")
        return 0
    else:
        print("\n❌ Build failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
