"""Minimal tests for ML-based file cleanup without heavy dependencies."""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from file_cleanup.ml.analyzer import MLFileAnalyzer
from file_cleanup.ml.model import FileCleanupModel
from file_cleanup.ml.trainer import FileCleanupTrainer


class TestMLFileAnalyzerMinimal(unittest.TestCase):
    """Minimal test cases for MLFileAnalyzer class without heavy dependencies."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_ml_analyzer_"))
        self.model_dir = self.test_dir / "models"
        self.model_dir.mkdir(exist_ok=True)
        
        # Create test files
        self.create_test_files()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Create test files with different characteristics."""
        # Create some temporary files
        (self.test_dir / "temp_file.tmp").touch()
        (self.test_dir / "cache_file.cache").touch()
        
        # Create some log files
        log_dir = self.test_dir / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("This is a log file\n" * 10)
        
        # Create an old log file
        old_log = log_dir / "old_app.log"
        old_log.touch()
        old_time = datetime.now() - timedelta(days=60)
        os.utime(old_log, (old_log.stat().st_atime, old_time.timestamp()))
    
    def test_analyze_file_temp_file(self):
        """Test analyzing a temporary file."""
        analyzer = MLFileAnalyzer(root_path=str(self.test_dir))  # Should use rule-based by default if no model path provided
        file_info = {
            'path': str(self.test_dir / "temp_file.tmp"),
            'size': 1024,
            'modified': datetime.now(),
            'accessed': datetime.now()
        }
        
        result = analyzer.analyze_file(file_info)
        self.assertTrue(result['should_delete'])
        self.assertIn('Temporary file pattern', ' '.join(result['reasons']))
    
    def test_analyze_file_old_log(self):
        """Test analyzing an old log file."""
        analyzer = MLFileAnalyzer(root_path=str(self.test_dir))  # Should use rule-based by default if no model path provided
        old_time = datetime.now() - timedelta(days=60)
        
        file_info = {
            'path': str(self.test_dir / "logs" / "old_app.log"),
            'size': 1024,
            'modified': old_time,
            'accessed': old_time
        }
        
        result = analyzer.analyze_file(file_info)
        self.assertTrue(result['should_delete'])
        self.assertIn('Old log file', ' '.join(result['reasons']))
    
    def test_analyze_directory(self):
        """Test analyzing a directory of files."""
        # Print debug information
        print("\nTest directory contents:")
        for f in self.test_dir.rglob('*'):
            print(f"- {f.relative_to(self.test_dir)}")
            
        analyzer = MLFileAnalyzer(root_path=str(self.test_dir))
        results = analyzer.analyze_directory(self.test_dir, min_confidence=0.5)
        
        # Print analysis results for debugging
        print("\nAnalysis results:")
        for r in results:
            print(f"- {r['path']}: delete={r['should_delete']}, reasons={r['reasons']}")
        
        # Get all files that were marked for deletion
        delete_paths = {str(Path(r['path']).relative_to(self.test_dir)) 
                       for r in results if r['should_delete']}
        
        # Print files marked for deletion
        print("\nFiles marked for deletion:", delete_paths)
        
        # Check that we have the expected files in results
        self.assertIn("temp_file.tmp", delete_paths, 
                     f"Expected temp_file.tmp to be marked for deletion. Found: {delete_paths}")
        self.assertIn("logs/old_app.log", delete_paths,
                     f"Expected logs/old_app.log to be marked for deletion. Found: {delete_paths}")


if __name__ == "__main__":
    unittest.main()
