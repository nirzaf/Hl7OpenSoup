#!/usr/bin/env python3
"""
Setup script for HL7 OpenSoup - Advanced HL7 Desktop Viewer and Editor
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hl7-opensoup",
    version="1.0.0",
    author="HL7 OpenSoup Development Team",
    author_email="dev@hl7opensoup.com",
    description="Advanced HL7 Desktop Viewer and Editor - A Python-based replica of HL7 Soup",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hl7-opensoup",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "packaging": [
            "pyinstaller>=6.0.0",
            "cx-freeze>=6.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hl7-opensoup=hl7opensoup.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hl7opensoup": [
            "config/*.yaml",
            "schemas/*.json",
            "resources/*.png",
            "resources/*.ico",
        ],
    },
)
