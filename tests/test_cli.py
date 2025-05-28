"""Tests for the command-line interface of file-cleanup-utility."""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from file_cleanup.cli import cli


class TestCLI:
    """Test cases for the command-line interface."""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path: Path):
        """Set up test environment for each test method."""
        self.runner = CliRunner()
        self.test_dir = tmp_path / "test_files"
        self.test_dir.mkdir()
        
        # Create some test files
        (self.test_dir / "file1.txt").write_text("This is a test file.")
        (self.test_dir / "file2.txt").write_text("This is another test file.")
        (self.test_dir / "file3.txt").write_text("This is a test file.")  # Duplicate
        
        # Create a subdirectory
        (self.test_dir / "subdir").mkdir()
        (self.test_dir / "subdir" / "nested.txt").write_text("Nested file")
        
        # Create an empty file
        (self.test_dir / "empty.txt").touch()
        
        # Store original working directory
        self.original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        yield
        
        # Restore original working directory
        os.chdir(self.original_cwd)

    def test_help_command(self):
        """Test the help command output."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Show this message and exit." in result.output
        assert "scan" in result.output
        assert "analyze" in result.output
        assert "clean" in result.output
        assert "duplicates" in result.output
        assert "report" in result.output

    def test_scan_command_basic(self):
        """Test the scan command with default options."""
        result = self.runner.invoke(cli, ["scan", str(self.test_dir)])
        assert result.exit_code == 0
        assert "Scanning directory:" in result.output
        assert "Found 5 files" in result.output
        assert "file1.txt" in result.output
        assert "subdir/nested.txt" in result.output

    def test_scan_command_with_exclude(self):
        """Test the scan command with exclude pattern."""
        result = self.runner.invoke(
            cli, 
            ["scan", str(self.test_dir), "--exclude", "**/*.txt"]
        )
        assert result.exit_code == 0
        assert "Found 0 files" in result.output

    def test_scan_command_output_file(self, tmp_path: Path):
        """Test the scan command with output to file."""
        output_file = tmp_path / "scan_results.json"
        result = self.runner.invoke(
            cli,
            ["scan", str(self.test_dir), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify the output file contains valid JSON
        with open(output_file) as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 5  # Should have 5 files
            assert any("file1.txt" in item["path"] for item in data)

    def test_analyze_command_basic(self):
        """Test the analyze command with default options."""
        result = self.runner.invoke(
            cli,
            ["analyze", str(self.test_dir), "--min-age", "0"]
        )
        assert result.exit_code == 0
        assert "Analyzing files in:" in result.output
        assert "Found 1 empty files" in result.output
        assert "Found 1 groups of duplicates" in result.output

    def test_analyze_command_output_file(self, tmp_path: Path):
        """Test the analyze command with output to file."""
        output_file = tmp_path / "analysis_results.json"
        result = self.runner.invoke(
            cli,
            [
                "analyze", 
                str(self.test_dir), 
                "--output", str(output_file),
                "--min-age", "0"
            ]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify the output file contains valid JSON
        with open(output_file) as f:
            data = json.load(f)
            assert "duplicates" in data
            assert "empty_files" in data
            assert "old_files" in data
            assert "orphaned_files" in data

    def test_duplicates_command(self):
        """Test the duplicates command."""
        result = self.runner.invoke(
            cli,
            ["duplicates", str(self.test_dir)]
        )
        assert result.exit_code == 0
        assert "Found 1 groups of duplicates" in result.output
        assert "file1.txt" in result.output
        assert "file3.txt" in result.output

    def test_clean_command_dry_run(self):
        """Test the clean command in dry-run mode."""
        # First analyze to get a report
        report_file = self.test_dir / "report.json"
        self.runner.invoke(
            cli,
            ["analyze", str(self.test_dir), "--output", str(report_file), "--min-age", "0"]
        )
        
        # Test clean with dry-run
        result = self.runner.invoke(
            cli,
            ["clean", str(self.test_dir), "--report", str(report_file), "--dry-run"]
        )
        
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Would delete" in result.output
        
        # Verify no files were actually deleted
        assert (self.test_dir / "empty.txt").exists()

    @patch("file_cleanup.cli.FileCleaner.clean_files")
    def test_clean_command_confirm(self, mock_clean_files: MagicMock):
        """Test the clean command with confirmation."""
        # Mock the clean_files method to avoid actual file operations
        mock_clean_files.return_value = {
            "deleted": ["empty.txt"],
            "skipped": [],
            "errors": []
        }
        
        # Create a report file
        report_file = self.test_dir / "report.json"
        with open(report_file, "w") as f:
            json.dump({
                "empty_files": [{"path": str(self.test_dir / "empty.txt")}],
                "duplicates": [],
                "old_files": [],
                "orphaned_files": []
            }, f)
        
        # Test clean with confirmation (simulate user input 'y')
        result = self.runner.invoke(
            cli,
            ["clean", str(self.test_dir), "--report", str(report_file)],
            input="y\n"
        )
        
        assert result.exit_code == 0
        assert "1 files will be deleted" in result.output
        assert "Cleaning complete" in result.output
        mock_clean_files.assert_called_once()

    def test_report_command(self, tmp_path: Path):
        """Test the report command."""
        # First analyze to create a report
        report_file = tmp_path / "analysis_report.json"
        self.runner.invoke(
            cli,
            ["analyze", str(self.test_dir), "--output", str(report_file), "--min-age", "0"]
        )
        
        # Generate a report
        output_file = tmp_path / "report.html"
        result = self.runner.invoke(
            cli,
            ["report", str(report_file), "--format", "html", "--output", str(output_file)]
        )
        
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Report generated successfully" in result.output
        
        # Verify the output file contains expected content
        with open(output_file) as f:
            content = f.read()
            assert "<html" in content
            assert "File Analysis Report" in content

    def test_invalid_command(self):
        """Test an invalid command."""
        result = self.runner.invoke(cli, ["invalid-command"])
        assert result.exit_code == 2
        assert "No such command" in result.output

    def test_missing_directory(self):
        """Test with a non-existent directory."""
        result = self.runner.invoke(cli, ["scan", "/nonexistent/directory"])
        assert result.exit_code != 0
        assert "does not exist" in result.output

    @patch("file_cleanup.cli.FileAnalyzer")
    def test_analyze_command_error_handling(self, mock_analyzer: MagicMock):
        """Test error handling in the analyze command."""
        # Configure the mock to raise an exception
        mock_instance = mock_analyzer.return_value
        mock_instance.analyze_files.side_effect = Exception("Test error")
        
        result = self.runner.invoke(
            cli,
            ["analyze", str(self.test_dir)]
        )
        
        assert result.exit_code == 1
        assert "Error analyzing files" in result.output
        assert "Test error" in result.output

    def test_version_command(self):
        """Test the version command."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        # Should print something like "file-cleanup-utility, version 0.1.0"
        assert "file-cleanup-utility, version" in result.output
