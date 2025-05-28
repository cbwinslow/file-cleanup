"""Pytest configuration and fixtures for file-cleanup-utility tests."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing and clean up afterward."""
    tmp_dir = tempfile.mkdtemp(prefix="file_cleanup_test_")
    try:
        yield Path(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_files(temp_dir: Path) -> Path:
    """Create a directory with test files."""
    # Create some test files
    (temp_dir / "file1.txt").write_text("This is a test file.")
    (temp_dir / "file2.txt").write_text("This is another test file.")
    (temp_dir / "file3.txt").write_text("This is a test file.")  # Duplicate content
    
    # Create a subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file content")
    
    # Create an empty file
    (temp_dir / "empty.txt").touch()
    
    return temp_dir


@pytest.fixture(scope="session")
def sample_config() -> str:
    """Return a sample configuration string."""
    return """
    [general]
    default_age_days = 30
    similarity_threshold = 0.8
    max_file_size = "1GB"
    
    [paths]
    exclude = ["**/node_modules/**", "**/.git/**"]
    include = ["**/*.txt", "**/*.md"]
    
    [cleanup]
    move_to_trash = true
    backup_before_delete = false
    """
