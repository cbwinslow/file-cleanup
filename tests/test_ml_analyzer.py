"""Tests for the ML-based file analyzer."""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from file_cleanup.ml.analyzer import MLFileAnalyzer
from file_cleanup.ml.model import FileCleanupModel
from file_cleanup.ml.trainer import FileCleanupTrainer


class TestMLFileAnalyzer(unittest.TestCase):
    """Test cases for MLFileAnalyzer class."""

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
        (log_dir / "app.log").touch()
        
        # Create an old log file
        old_log = log_dir / "old_app.log"
        old_log.touch()
        old_time = datetime.now() - timedelta(days=60)
        os.utime(old_log, (old_log.stat().st_atime, old_time.timestamp()))
        
        # Create a download file
        download_dir = self.test_dir / "downloads"
        download_dir.mkdir()
        (download_dir / "archive.zip").touch()
    
    def test_analyze_file_temp_file(self):
        """Test analyzing a temporary file."""
        analyzer = MLFileAnalyzer()
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
        analyzer = MLFileAnalyzer()
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
    
    def test_analyze_file_cache(self):
        """Test analyzing a cache file."""
        analyzer = MLFileAnalyzer()
        file_info = {
            'path': str(self.test_dir / "cache_file.cache"),
            'size': 5 * 1024 * 1024,  # 5MB
            'modified': datetime.now(),
            'accessed': datetime.now()
        }
        
        result = analyzer.analyze_file(file_info)
        self.assertTrue(result['should_delete'])
        self.assertIn('Cache file', ' '.join(result['reasons']))
    
    def test_analyze_directory(self):
        """Test analyzing a directory of files."""
        analyzer = MLFileAnalyzer()
        results = analyzer.analyze_directory(self.test_dir, min_confidence=0.5)
        
        # We should have at least the temp file and old log file
        self.assertGreaterEqual(len(results), 2)
        
        # Check that we have the expected files in results
        paths = {str(Path(r['path']).relative_to(self.test_dir)) for r in results}
        self.assertIn(Path("temp_file.tmp"), paths)
        self.assertIn(Path("logs") / "old_app.log", paths)
    
    def test_train_and_use_model(self):
        """Test training and using a model."""
        # Create a trainer and train a model
        trainer = FileCleanupTrainer()
        model = trainer.train_model()
        
        # Save the model
        model_path = self.model_dir / "test_model"
        model.save(model_path)
        
        # Create an analyzer with the trained model
        analyzer = MLFileAnalyzer(model_path=model_path)
        
        # Test the model on a file
        file_info = {
            'path': str(self.test_dir / "temp_file.tmp"),
            'size': 1024,
            'modified': datetime.now(),
            'accessed': datetime.now()
        }
        
        result = analyzer.analyze_file(file_info)
        self.assertTrue(result['model_used'])
        
        # The model might or might not recommend deletion based on training data
        # Just verify the structure of the result
        self.assertIn('should_delete', result)
        self.assertIn('confidence', result)
        self.assertIn('reasons', result)


if __name__ == "__main__":
    unittest.main()
