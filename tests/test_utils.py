"""Tests for utility functions in file-cleanup-utility."""

import os
import stat
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pytest

from file_cleanup.utils import (
    FileInfo,
    calculate_file_hash,
    format_file_size,
    get_file_info,
    is_binary_file,
    safe_delete_file,
    validate_directory,
)


def test_validate_directory_valid(tmp_path: Path):
    """Test that a valid directory passes validation."""
    # Create a test directory
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Should not raise an exception
    validate_directory(str(test_dir))


def test_validate_directory_nonexistent():
    """Test that a non-existent directory raises an error."""
    with pytest.raises(ValueError, match="does not exist"):
        validate_directory("/nonexistent/path/that/should/not/exist")


def test_validate_directory_not_a_directory(tmp_path: Path):
    """Test that a file path (not a directory) raises an error."""
    # Create a file, not a directory
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test")
    
    with pytest.raises(ValueError, match="is not a directory"):
        validate_directory(str(test_file))


def test_validate_directory_no_permission(tmp_path: Path):
    """Test that a directory without read permission raises an error."""
    if os.name == 'nt':  # Skip on Windows
        pytest.skip("Permissions test not reliable on Windows")
    
    # Create a test directory
    test_dir = tmp_path / "no_permission_dir"
    test_dir.mkdir()
    
    # Remove read permissions
    original_mode = test_dir.stat().st_mode
    test_dir.chmod(0o000)  # No permissions
    
    try:
        with pytest.raises(PermissionError, match="permission"):
            validate_directory(str(test_dir))
    finally:
        # Restore permissions so the directory can be cleaned up
        test_dir.chmod(original_mode)


def test_get_file_info_basic(tmp_path: Path):
    """Test basic file info retrieval."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    content = "Hello, World!"
    test_file.write_text(content)
    
    # Get file info
    file_info = get_file_info(test_file)
    
    # Check basic attributes
    assert file_info.path == test_file
    assert file_info.size == len(content)
    assert file_info.extension == ".txt"
    assert file_info.mime_type.startswith("text/")
    assert not file_info.is_hidden
    assert not file_info.is_symlink
    assert file_info.permissions is not None
    assert file_info.created is not None
    assert file_info.modified is not None
    assert file_info.accessed is not None


def test_get_file_info_hidden(tmp_path: Path):
    """Test that hidden files are correctly identified."""
    # Create a hidden file (naming convention for hidden files on Unix-like systems)
    test_file = tmp_path / ".hidden_file"
    test_file.write_text("hidden")
    
    file_info = get_file_info(test_file)
    
    # On Unix-like systems, this should be hidden; on Windows, it depends on attributes
    if os.name != 'nt':
        assert file_info.is_hidden
    else:
        # On Windows, test the hidden attribute directly
        assert (file_info.path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) != 0


def test_calculate_file_hash(tmp_path: Path):
    """Test file hash calculation."""
    # Create a test file with known content
    test_file = tmp_path / "test_hash.txt"
    content = "This is a test file for hashing."
    test_file.write_text(content)
    
    # Calculate hash
    file_hash = calculate_file_hash(test_file)
    
    # Should be a non-empty string
    assert isinstance(file_hash, str)
    assert len(file_hash) == 64  # SHA-256 produces 64-character hashes
    
    # Same content should produce same hash
    test_file2 = tmp_path / "test_hash_copy.txt"
    test_file2.write_text(content)
    assert calculate_file_hash(test_file2) == file_hash
    
    # Different content should produce different hash
    test_file3 = tmp_path / "test_hash_different.txt"
    test_file3.write_text(content + " ")
    assert calculate_file_hash(test_file3) != file_hash


def test_is_binary_file(tmp_path: Path):
    """Test binary file detection."""
    # Create a text file
    text_file = tmp_path / "text.txt"
    text_file.write_text("This is a text file.")
    assert not is_binary_file(text_file)
    
    # Create a binary file
    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')
    assert is_binary_file(binary_file)


def test_format_file_size():
    """Test file size formatting."""
    assert format_file_size(0) == "0 B"
    assert format_file_size(1023) == "1023 B"
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1024 * 1024) == "1.0 MB"
    assert format_file_size(1024 * 1024 * 1.5) == "1.5 MB"
    assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
    assert format_file_size(1024 * 1024 * 1024 * 1024 * 1024) == "1024.0 TB"


def test_safe_delete_file(tmp_path: Path):
    """Test safe file deletion."""
    # Create a test file
    test_file = tmp_path / "to_delete.txt"
    test_file.write_text("Delete me")
    
    # File should exist initially
    assert test_file.exists()
    
    # Delete the file
    safe_delete_file(test_file)
    
    # File should no longer exist
    assert not test_file.exists()


def test_safe_delete_file_nonexistent(tmp_path: Path):
    """Test that deleting a non-existent file doesn't raise an error."""
    test_file = tmp_path / "nonexistent.txt"
    
    # Should not raise an exception
    safe_delete_file(test_file)


def test_safe_delete_file_readonly(tmp_path: Path):
    """Test that read-only files can be deleted."""
    if os.name == 'nt':  # Skip on Windows
        pytest.skip("Read-only test not reliable on Windows")
    
    # Create a read-only file
    test_file = tmp_path / "readonly.txt"
    test_file.write_text("Read only content")
    test_file.chmod(0o444)  # Read-only
    
    try:
        # Should be able to delete even if read-only
        safe_delete_file(test_file)
        assert not test_file.exists()
    finally:
        # Ensure the file is removed even if the test fails
        if test_file.exists():
            test_file.chmod(0o666)  # Restore permissions
            test_file.unlink()
