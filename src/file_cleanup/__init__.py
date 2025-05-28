"""
File Cleanup Utility - A powerful tool for analyzing and cleaning up your file system.
"""

__version__ = "0.1.0"

from .file_analyzer import FileAnalyzer
from .cli import main

__all__ = ['FileAnalyzer', 'main']
