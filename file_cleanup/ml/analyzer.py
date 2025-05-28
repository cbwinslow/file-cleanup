"""ML-based file analyzer for file cleanup."""

import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from ..core.analyzer import FileAnalyzer as BaseFileAnalyzer
from .model import FileCleanupModel, TENSORFLOW_AVAILABLE

logger = logging.getLogger(__name__)

class MLFileAnalyzer:
    """ML-powered file analyzer that extends the base file analyzer with ML capabilities."""
    
    def __init__(self, model_path: Optional[str] = None, model_type: str = 'random_forest', root_path: Optional[str] = None):
        """Initialize the ML file analyzer.
        
        Args:
            model_path: Path to a pre-trained model. If None, uses default rules.
            model_type: Type of model to use if no model is loaded ('random_forest' or 'neural_network')
            root_path: Root directory path for the base analyzer
        """
        self.model = None
        self.model_type = model_type
        self.model_path = model_path
        self.root_path = root_path or os.getcwd()
        self.base_analyzer = BaseFileAnalyzer(root_path=self.root_path)
        
        # Default rules if no model is loaded
        self.default_rules = [
            self._is_temp_file,
            self._is_old_log_file,
            self._is_cache_file,
            self._is_old_download
        ]
        
        # Try to load the model if path is provided
        if model_path and Path(model_path).exists():
            try:
                self.model = FileCleanupModel.load(model_path)
                logger.info(f"Loaded ML model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
    
    def analyze_file(self, file_info: Dict) -> Dict:
        """Analyze a file and return a recommendation.
        
        Args:
            file_info: Dictionary containing file information
            
        Returns:
            Dictionary with analysis results
        """
        result = {
            'path': file_info['path'],
            'size': file_info.get('size', 0),
            'modified': file_info.get('modified', datetime.now()),
            'accessed': file_info.get('accessed', datetime.now()),
            'should_delete': False,
            'confidence': 0.0,
            'reasons': [],
            'model_used': False
        }
        
        # Use ML model if available
        if self.model:
            try:
                should_delete, confidence = self.model.predict(file_info)
                result['should_delete'] = should_delete
                result['confidence'] = confidence
                result['model_used'] = True
                
                if should_delete:
                    result['reasons'].append(f"ML model prediction (confidence: {confidence:.2f})")
                return result
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}. Falling back to rules.")
        
        # Fall back to rule-based analysis
        return self._analyze_with_rules(file_info)
    
    def _analyze_with_rules(self, file_info: Dict) -> Dict:
        """Analyze a file using rule-based approach."""
        result = {
            'path': file_info['path'],
            'size': file_info.get('size', 0),
            'modified': file_info.get('modified', datetime.now()),
            'accessed': file_info.get('accessed', datetime.now()),
            'should_delete': False,
            'confidence': 0.0,
            'reasons': [],
            'model_used': False
        }
        
        # Apply each rule
        for rule in self.default_rules:
            should_delete, reason = rule(file_info)
            if should_delete:
                result['should_delete'] = True
                result['reasons'].append(reason)
        
        # Calculate confidence based on number of matching rules
        if result['reasons']:
            result['confidence'] = min(0.9, 0.3 * len(result['reasons']))  # Cap at 0.9 for rule-based
        
        return result
    
    def analyze_directory(
        self, 
        directory: Union[str, Path], 
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """Analyze all files in a directory.
        
        Args:
            directory: Directory to analyze
            include_patterns: List of file patterns to include
            exclude_patterns: List of file patterns to exclude
            min_confidence: Minimum confidence threshold for recommendations
            
        Returns:
            List of analysis results for files that should be deleted
        """
        directory = Path(directory).resolve()
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        logger.info(f"Analyzing directory: {directory}")
        logger.info(f"Include patterns: {include_patterns}")
        logger.info(f"Exclude patterns: {exclude_patterns}")
        
        # Use base analyzer to scan directory
        self.base_analyzer.root_path = directory
        self.base_analyzer.include_patterns = include_patterns or ['**/*']
        self.base_analyzer.exclude_patterns = exclude_patterns or []
        self.base_analyzer.scan_directory()
        
        logger.info(f"Found {len(self.base_analyzer.files)} files to analyze")
        
        # Analyze each file
        results = []
        for file_info in self.base_analyzer.files:
            try:
                logger.debug(f"Analyzing file: {file_info.get('path')}")
                analysis = self.analyze_file(file_info)
                logger.debug(f"Analysis result: {analysis}")
                
                if analysis['should_delete']:
                    logger.info(f"File marked for deletion: {file_info.get('path')} (confidence: {analysis['confidence']:.2f}, reasons: {analysis['reasons']})")
                    if analysis['confidence'] >= min_confidence:
                        results.append(analysis)
                    else:
                        logger.debug(f"Skipping file due to low confidence: {file_info.get('path')} ({analysis['confidence']:.2f} < {min_confidence})")
            except Exception as e:
                logger.error(f"Error analyzing {file_info.get('path', 'unknown')}: {e}")
        
        logger.info(f"Analysis complete. Found {len(results)} files to delete")
        
        return results
    
    # Rule-based analysis functions
    def _is_temp_file(self, file_info: Dict) -> Tuple[bool, str]:
        """Check if file is a temporary file."""
        path = Path(file_info['path'])
        temp_indicators = ['~$', '.tmp', '.temp', '.bak', '.swp', '.swp']
        
        if any(indicator in path.name.lower() for indicator in temp_indicators):
            return True, "Temporary file pattern detected"
            
        return False, ""
    
    def _is_old_log_file(self, file_info: Dict, days_threshold: int = 30) -> Tuple[bool, str]:
        """Check if file is an old log file."""
        path = Path(file_info['path'])
        
        if path.suffix.lower() in ['.log', '.log.1', '.log.2']:
            modified = file_info.get('modified', datetime.now())
            age = (datetime.now() - modified).days
            
            if age > days_threshold:
                return True, f"Old log file ({age} days old)"
                
        return False, ""
    
    def _is_cache_file(self, file_info: Dict, max_size_mb: int = 10) -> Tuple[bool, str]:
        """Check if file is a cache file that can be safely deleted."""
        path = Path(file_info['path'])
        cache_indicators = ['cache', 'Cache', 'Caches', '.cache']
        
        if any(indicator in str(path) for indicator in cache_indicators):
            size_mb = file_info.get('size', 0) / (1024 * 1024)  # Convert to MB
            if size_mb <= max_size_mb:
                return True, f"Cache file ({size_mb:.1f}MB)"
                
        return False, ""
    
    def _is_old_download(self, file_info: Dict, days_threshold: int = 90) -> Tuple[bool, str]:
        """Check if file is an old download."""
        path = str(file_info['path']).lower()
        
        if 'download' in path or 'downloaded' in path:
            modified = file_info.get('modified', datetime.now())
            age = (datetime.now() - modified).days
            
            if age > days_threshold:
                return True, f"Old download ({age} days old)"
                
        return False, ""
    
    @classmethod
    def train_default_model(
        cls, 
        output_dir: str = 'models/file_cleanup_model',
        model_type: str = 'random_forest'
    ) -> 'MLFileAnalyzer':
        """Train a default model and return a new analyzer instance.
        
        Args:
            output_dir: Directory to save the trained model
            model_type: Type of model to train ('random_forest' or 'neural_network')
            
        Returns:
            A new MLFileAnalyzer instance with the trained model
        """
        from .trainer import train_default_model
        
        # Train the model
        metrics = train_default_model(output_dir)
        logger.info(f"Trained model with accuracy: {metrics['accuracy']:.2f}")
        
        # Return a new analyzer with the trained model
        return cls(model_path=output_dir, model_type=model_type)
