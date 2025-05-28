"""Tests for core functionality of file-cleanup-utility."""

import os
import time
from pathlib import Path
from typing import Dict, List, Set

import pytest

from file_cleanup.core.analyzer import FileAnalyzer
from file_cleanup.utils import FileInfo, get_file_info


def test_file_analyzer_initialization():
    """Test that FileAnalyzer initializes correctly."""
    analyzer = FileAnalyzer()
    assert analyzer is not None


def test_scan_directory(test_files: Path):
    """Test that scan_directory finds all files."""
    analyzer = FileAnalyzer()
    files = list(analyzer.scan_directory(test_files))
    
    # Should find all files including those in subdirectories
    assert len(files) == 5  # file1.txt, file2.txt, file3.txt, empty.txt, subdir/nested.txt
    
    # Check that all paths are Path objects
    assert all(isinstance(f, Path) for f in files)


def test_find_duplicates(test_files: Path):
    """Test that duplicate files are correctly identified."""
    analyzer = FileAnalyzer()
    files = list(analyzer.scan_directory(test_files))
    file_infos = [get_file_info(f) for f in files]
    
    # Group files by content hash
    duplicates = analyzer._find_duplicates(file_infos)
    
    # file1.txt and file3.txt have the same content
    assert len(duplicates) == 1  # One group of duplicates
    assert len(duplicates[0]) == 2  # Two files in the group
    assert any("file1.txt" in str(f.path) for f in duplicates[0])
    assert any("file3.txt" in str(f.path) for f in duplicates[0])


def test_find_old_files(test_files: Path):
    """Test that old files are correctly identified."""
    analyzer = FileAnalyzer()
    
    # Make one file old by setting its modification time to 100 days ago
    old_file = test_files / "file1.txt"
    old_time = time.time() - (100 * 24 * 60 * 60)  # 100 days ago
    os.utime(old_file, (old_time, old_time))
    
    files = list(analyzer.scan_directory(test_files))
    file_infos = [get_file_info(f) for f in files]
    
    # Find files older than 30 days
    old_files = analyzer._find_old_files(file_infos, age_days=30)
    
    # Only the file we made old should be in the results
    assert len(old_files) == 1
    assert "file1.txt" in str(old_files[0].path)


def test_find_empty_files(test_files: Path):
    """Test that empty files are correctly identified."""
    analyzer = FileAnalyzer()
    files = list(analyzer.scan_directory(test_files))
    file_infos = [get_file_info(f) for f in files]
    
    empty_files = analyzer._find_empty_files(file_infos)
    
    # Only the empty file we created should be in the results
    assert len(empty_files) == 1
    assert "empty.txt" in str(empty_files[0].path)


def test_analyze_files(test_files: Path):
    """Test the main analyze_files method."""
    analyzer = FileAnalyzer()
    results = analyzer.analyze_files(str(test_files))
    
    # Check that we have all the expected result keys
    assert "duplicates" in results
    assert "old_files" in results
    assert "empty_files" in results
    assert "orphaned_files" in results
    
    # We know we should have at least one empty file and one group of duplicates
    assert len(results["empty_files"]) >= 1
    assert len(results["duplicates"]) >= 1


def test_find_orphaned_files(test_files: Path):
    """Test that orphaned files are correctly identified."""
    analyzer = FileAnalyzer()
    
    # Create a file that might be considered orphaned
    orphaned = test_files / "orphaned.log"
    orphaned.write_text("Log file that might be orphaned")
    
    files = list(analyzer.scan_directory(test_files))
    file_infos = [get_file_info(f) for f in files]
    
    # Mark all files except our test file as referenced
    referenced_files = {str(f.path) for f in file_infos if f.path != orphaned}
    
    # Find orphaned files (should be our test file)
    orphaned_files = analyzer._find_orphaned_files(file_infos, referenced_files)
    
    assert len(orphaned_files) == 1
    assert orphaned_files[0].path == orphaned


def test_cluster_similar_files(test_files: Path):
    """Test that similar files are correctly clustered."""
    analyzer = FileAnalyzer()
    
    # Create some similar text files
    similar1 = test_files / "similar1.txt"
    similar2 = test_files / "similar2.txt"
    different = test_files / "different.txt"
    
    similar1.write_text("This is a test file with some content for testing similarity.")
    similar2.write_text("This is a test file with some content for testing similarity!!!")
    different.write_text("This is a completely different file with unique content.")
    
    files = list(analyzer.scan_directory(test_files))
    file_infos = [get_file_info(f) for f in files]
    
    # Cluster similar files with a high threshold
    clusters = analyzer._cluster_similar_files(file_infos, similarity_threshold=0.8)
    
    # We should have at least one cluster with our similar files
    assert len(clusters) >= 1
    
    # Check that our similar files are in the same cluster
    similar_cluster = next(
        (c for c in clusters 
         if any("similar1.txt" in str(f.path) for f in c) and 
            any("similar2.txt" in str(f.path) for f in c)),
        None
    )
    
    assert similar_cluster is not None, "Similar files should be in the same cluster"
    assert len(similar_cluster) >= 2, "Cluster should contain at least the two similar files"
