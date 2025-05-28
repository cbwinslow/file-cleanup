"""Tests for the main module of file-cleanup-utility."""

import sys
from unittest.mock import patch, MagicMock

import pytest

# Import the main module
import file_cleanup


def test_main_import():
    """Test that the main module can be imported."""
    assert file_cleanup is not None
    assert hasattr(file_cleanup, "__version__")
    assert isinstance(file_cleanup.__version__, str)


def test_main_function(capsys):
    """Test the main function execution."""
    with patch.object(sys, 'argv', ['file_cleanup', '--version']):
        with patch('file_cleanup.cli.cli') as mock_cli:
            # Mock the cli function to avoid actual execution
            mock_cli.side_effect = SystemExit(0)
            
            # Import here to avoid side effects during test collection
            from file_cleanup.main import main
            
            # Call the main function
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Verify the exit code
            assert exc_info.value.code == 0
            
            # Verify the cli function was called
            mock_cli.assert_called_once()


def test_main_module_execution():
    """Test that the module can be executed with -m flag."""
    with patch('file_cleanup.cli.cli') as mock_cli:
        # Mock the cli function to avoid actual execution
        mock_cli.side_effect = SystemExit(0)
        
        # Simulate running the module with -m
        with patch('sys.argv', ['-m', 'file_cleanup', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                # Import and execute the module
                import runpy
                runpy.run_module('file_cleanup', run_name='__main__')
            
            # Verify the exit code
            assert exc_info.value.code == 0
            
            # Verify the cli function was called
            mock_cli.assert_called_once()


def test_version():
    """Test the version string format."""
    from file_cleanup import __version__
    # Version should be in format X.Y.Z
    import re
    assert re.match(r'^\d+\.\d+\.\d+$', __version__), \
        f"Version {__version__} is not in X.Y.Z format"
