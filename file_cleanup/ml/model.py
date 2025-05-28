"""Machine learning model for file cleanup recommendations."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

# Try to import TensorFlow, but make it optional
try:
    import tensorflow as tf
    from tensorflow.keras.layers import Dense, Dropout
    from tensorflow.keras.models import Sequential, load_model
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    load_model = None
    Sequential = None
    Dense = None
    Dropout = None

logger = logging.getLogger(__name__)

class FileCleanupModel:
    """Machine learning model for predicting files that can be safely deleted."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """Initialize the file cleanup model.
        
        Args:
            model_type: Type of model to use ('random_forest' or 'neural_network')
        """
        self.model_type = model_type
        self.model = None
        self.feature_columns = [
            'file_size', 'days_since_modified', 'days_since_accessed',
            'extension', 'is_hidden', 'is_system', 'has_temp_pattern'
        ]
        self.text_columns = ['filename', 'path']
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
    def extract_features(self, file_info: Dict) -> Dict:
        """Extract features from file information dictionary."""
        path = Path(file_info['path'])
        now = datetime.now()
        
        features = {
            'file_size': file_info.get('size', 0),
            'days_since_modified': (now - file_info.get('modified', now)).days,
            'days_since_accessed': (now - file_info.get('accessed', now)).days,
            'extension': path.suffix.lower(),
            'is_hidden': path.name.startswith('.'),
            'is_system': bool(file_info.get('is_system', False)),
            'has_temp_pattern': any(p in path.name.lower() for p in ['temp', 'tmp', '~$', '.bak']),
            'filename': path.stem,
            'path': str(path.parent)
        }
        
        return features
    
    def preprocess_data(self, X: pd.DataFrame) -> np.ndarray:
        """Preprocess the input data for model training/prediction."""
        # Preprocess numerical features
        num_features = X[['file_size', 'days_since_modified', 'days_since_accessed']]
        num_features = self.scaler.fit_transform(num_features)
        
        # Preprocess categorical features
        cat_features = X[['extension', 'is_hidden', 'is_system', 'has_temp_pattern']]
        cat_features = cat_features.apply(lambda col: self.label_encoder.fit_transform(col.astype(str)))
        
        # Preprocess text features
        text_features = self.vectorizer.fit_transform(X['filename'] + ' ' + X['path']).toarray()
        
        # Combine all features
        return np.hstack([num_features, cat_features, text_features])
    
    def train(self, X: pd.DataFrame, y: np.ndarray) -> None:
        """Train the model on the given data.
        
        Args:
            X: DataFrame containing file features
            y: Target labels (1 for delete, 0 for keep)
        """
        if self.model_type == 'neural_network':
            self._train_neural_network(X, y)
        else:
            self._train_random_forest(X, y)
    
    def _train_random_forest(self, X: pd.DataFrame, y: np.ndarray) -> None:
        """Train a random forest classifier."""
        X_processed = self.preprocess_data(X)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_processed, y)
    
    def _train_neural_network(self, X: pd.DataFrame, y: np.ndarray) -> None:
        """Train a neural network classifier."""
        X_processed = self.preprocess_data(X)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, y, test_size=0.2, random_state=42
        )
        
        # Define model
        input_shape = X_train.shape[1]
        
        self.model = models.Sequential([
            layers.Dense(128, activation='relu', input_shape=(input_shape,)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(1, activation='sigmoid')
        ])
        
        # Compile model
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Train model
        self.model.fit(
            X_train, y_train,
            epochs=10,
            batch_size=32,
            validation_data=(X_val, y_val),
            verbose=1
        )
    
    def predict(self, file_info: Dict) -> Tuple[bool, float]:
        """Predict whether a file should be deleted.
        
        Args:
            file_info: Dictionary containing file information
            
        Returns:
            Tuple of (should_delete, confidence)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
            
        # Extract features
        features = self.extract_features(file_info)
        X = pd.DataFrame([features])
        
        # Preprocess
        X_processed = self.preprocess_data(X)
        
        # Predict
        if self.model_type == 'neural_network':
            proba = self.model.predict(X_processed)[0][0]
        else:
            proba = self.model.predict_proba(X_processed)[0][1]
            
        should_delete = proba > 0.5
        confidence = proba if should_delete else 1 - proba
        
        return should_delete, float(confidence)
    
    def save(self, path: Union[str, Path]) -> None:
        """Save the model to disk."""
        if self.model is None:
            raise ValueError("Model has not been trained yet")
            
        model_data = {
            'model_type': self.model_type,
            'feature_columns': self.feature_columns,
            'text_columns': self.text_columns,
        }
        
        # Save model weights and metadata
        os.makedirs(path, exist_ok=True)
        
        if self.model_type == 'neural_network':
            self.model.save(os.path.join(path, 'model.h5'))
        else:
            joblib.dump(self.model, os.path.join(path, 'model.joblib'))
        
        # Save preprocessors
        joblib.dump(self.scaler, os.path.join(path, 'scaler.joblib'))
        joblib.dump(self.label_encoder, os.path.join(path, 'label_encoder.joblib'))
        joblib.dump(self.vectorizer, os.path.join(path, 'vectorizer.joblib'))
        
        # Save metadata
        with open(os.path.join(path, 'metadata.json'), 'w') as f:
            json.dump(model_data, f)
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'FileCleanupModel':
        """Load a trained model from disk."""
        # Load metadata
        with open(os.path.join(path, 'metadata.json'), 'r') as f:
            model_data = json.load(f)
        
        # Create model instance
        model = cls(model_type=model_data['model_type'])
        model.feature_columns = model_data['feature_columns']
        model.text_columns = model_data['text_columns']
        
        # Load preprocessors
        model.scaler = joblib.load(os.path.join(path, 'scaler.joblib'))
        model.label_encoder = joblib.load(os.path.join(path, 'label_encoder.joblib'))
        model.vectorizer = joblib.load(os.path.join(path, 'vectorizer.joblib'))
        
        # Load model
        if model.model_type == 'neural_network':
            model.model = models.load_model(os.path.join(path, 'model.h5'))
        else:
            model.model = joblib.load(os.path.join(path, 'model.joblib'))
        
        return model
