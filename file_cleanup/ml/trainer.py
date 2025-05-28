"""Module for training and evaluating file cleanup models."""

import os
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, accuracy_score

from .model import FileCleanupModel

logger = logging.getLogger(__name__)

class FileCleanupTrainer:
    """Class for training and evaluating file cleanup models."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """Initialize the trainer.
        
        Args:
            model_type: Type of model to train ('random_forest' or 'neural_network')
        """
        self.model_type = model_type
        self.model = FileCleanupModel(model_type=model_type)
        
    def generate_synthetic_data(self, n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
        """Generate synthetic training data for demonstration purposes.
        
        In a real-world scenario, you would replace this with actual file metadata
        from your system, labeled by users or based on file access patterns.
        """
        np.random.seed(42)
        random.seed(42)
        
        # Common file extensions
        extensions = ['.txt', '.log', '.tmp', '.bak', '.py', '.json', '.csv', '.xlsx', '.docx']
        
        # Common directories
        base_dirs = [
            '/home/user/documents',
            '/home/user/downloads',
            '/var/log',
            '/tmp',
            '/home/user/projects',
            '/home/user/desktop'
        ]
        
        # Generate synthetic file data
        data = []
        labels = []
        
        for _ in range(n_samples):
            # Random file properties
            ext = random.choice(extensions)
            is_temp = ext in ['.tmp', '.bak'] or random.random() < 0.1
            is_old = random.random() < 0.3
            is_large = random.random() < 0.2
            is_hidden = random.random() < 0.1
            is_system = random.random() < 0.05
            
            # Generate file path
            base_dir = random.choice(base_dirs)
            filename = f"{'temp_' if is_temp else ''}{random.randint(1000, 9999)}{ext}"
            filepath = os.path.join(base_dir, filename)
            
            # Generate timestamps
            now = datetime.now()
            modified_days_ago = random.randint(1, 365 * 3)  # Up to 3 years old
            accessed_days_ago = random.randint(1, 365)  # Up to 1 year since last access
            
            # Generate file size (in bytes)
            if is_large:
                size = random.randint(10 * 1024 * 1024, 100 * 1024 * 1024)  # 10MB - 100MB
            else:
                size = random.randint(1024, 10 * 1024 * 1024)  # 1KB - 10MB
            
            # Create file info
            file_info = {
                'path': filepath,
                'size': size,
                'modified': now - timedelta(days=modified_days_ago),
                'accessed': now - timedelta(days=accessed_days_ago),
                'is_hidden': is_hidden,
                'is_system': is_system
            }
            
            # Determine label (1 = delete, 0 = keep)
            # This is a simple heuristic - in practice, you'd use real labels
            should_delete = (
                is_temp or  # Temporary files
                (is_old and not is_large) or  # Old small files
                (ext in ['.log'] and modified_days_ago > 30) or  # Old logs
                (base_dir == '/tmp' and modified_days_ago > 7)  # Old temp files
            )
            
            # Add some noise
            should_delete = should_delete and random.random() > 0.1
            
            data.append(file_info)
            labels.append(1 if should_delete else 0)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df, np.array(labels)
    
    def train_and_evaluate(self, X: pd.DataFrame, y: np.ndarray, test_size: float = 0.2) -> Dict:
        """Train and evaluate the model.
        
        Args:
            X: DataFrame containing file features
            y: Target labels (1 for delete, 0 for keep)
            test_size: Fraction of data to use for testing
            
        Returns:
            Dictionary containing evaluation metrics
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train model
        logger.info(f"Training {self.model_type} model...")
        self.model.train(X_train, y_train)
        
        # Evaluate on test set
        logger.info("Evaluating model...")
        y_pred = []
        y_proba = []
        
        for _, row in X_test.iterrows():
            should_delete, confidence = self.model.predict(row.to_dict())
            y_pred.append(1 if should_delete else 0)
            y_proba.append(confidence if should_delete else 1 - confidence)
        
        # Calculate metrics
        report = classification_report(y_test, y_pred, output_dict=True)
        accuracy = accuracy_score(y_test, y_pred)
        
        metrics = {
            'accuracy': accuracy,
            'precision': report['weighted avg']['precision'],
            'recall': report['weighted avg']['recall'],
            'f1': report['weighted avg']['f1-score'],
            'class_report': report
        }
        
        return metrics
    
    def save_model(self, output_dir: str) -> None:
        """Save the trained model to disk.
        
        Args:
            output_dir: Directory to save the model to
        """
        os.makedirs(output_dir, exist_ok=True)
        self.model.save(output_dir)
        logger.info(f"Model saved to {output_dir}")
    
    def load_model(self, model_dir: str) -> None:
        """Load a trained model from disk.
        
        Args:
            model_dir: Directory containing the saved model
        """
        self.model = FileCleanupModel.load(model_dir)
        logger.info(f"Model loaded from {model_dir}")

def train_default_model(output_dir: str = 'models/file_cleanup_model') -> Dict:
    """Train a default model with synthetic data.
    
    This is a convenience function for quickly getting started.
    In production, you should train on real, labeled data.
    
    Args:
        output_dir: Directory to save the trained model
        
    Returns:
        Dictionary containing evaluation metrics
    """
    # Create trainer
    trainer = FileCleanupTrainer(model_type='random_forest')
    
    # Generate synthetic data
    logger.info("Generating synthetic training data...")
    X, y = trainer.generate_synthetic_data(n_samples=5000)
    
    # Train and evaluate
    metrics = trainer.train_and_evaluate(X, y)
    
    # Save model
    trainer.save_model(output_dir)
    
    return metrics
