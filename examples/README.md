# ML-Based File Cleanup Examples

This directory contains examples demonstrating how to use the ML-based file cleanup functionality.

## Demo Script

The `ml_cleanup_demo.py` script provides a complete demonstration of the ML-based file cleanup capabilities. It allows you to:

1. Set up a demo environment with sample files
2. Train a new ML model on the demo files
3. Analyze files using either the trained model or default rules
4. View and save cleanup recommendations

### Prerequisites

- Python 3.7+
- Dependencies listed in `requirements.txt`

### Running the Demo

1. **Basic usage** (uses default rule-based analyzer):
   ```bash
   python examples/ml_cleanup_demo.py
   ```

2. **Train a new model and analyze** (recommended for best results):
   ```bash
   python examples/ml_cleanup_demo.py --train
   ```

3. **Customize the demo directory**:
   ```bash
   python examples/ml_cleanup_demo.py --demo-dir ./my_demo_dir
   ```

4. **Adjust confidence threshold** (default: 0.7):
   ```bash
   python examples/ml_cleanup_demo.py --min-confidence 0.8
   ```

### Command Line Interface

The main CLI includes ML functionality through the `ml-analyze` command:

```bash
# Basic usage (uses default rules)
file-cleanup ml-analyze /path/to/directory

# Use a trained model
file-cleanup ml-analyze /path/to/directory --model-path ./path/to/model

# Train a new model
file-cleanup ml-analyze /path/to/directory --model-path ./new_model --train

# Adjust confidence threshold (0-1)
file-cleanup ml-analyze /path/to/directory --min-confidence 0.8
```

## Integration Example

Here's how to use the ML analyzer in your own code:

```python
from pathlib import Path
from file_cleanup.ml import MLFileAnalyzer

# Create an analyzer with default rules
analyzer = MLFileAnalyzer()

# Or load a trained model
# analyzer = MLFileAnalyzer(model_path="./path/to/model")

# Analyze a directory
results = analyzer.analyze_directory(
    directory=Path("/path/to/directory"),
    min_confidence=0.7  # Optional: minimum confidence threshold
)

# Process results
for result in results:
    if result['should_delete']:
        print(f"Delete {result['path']} (confidence: {result['confidence']:.2f})")
        print(f"  Reasons: {', '.join(result['reasons'])}")
```

## Training Your Own Model

To train a custom model on your own data:

```python
from file_cleanup.ml import FileCleanupTrainer

# Create and train a model
trainer = FileCleanupTrainer()
model = trainer.train_model()

# Save the model
model.save("./custom_model")

# You can then use this model with MLFileAnalyzer
from file_cleanup.ml import MLFileAnalyzer
analyzer = MLFileAnalyzer(model_path="./custom_model")
```

## Understanding the Results

The analyzer returns a list of dictionaries with the following structure:

```python
{
    'path': '/path/to/file',
    'size': 1024,  # in bytes
    'modified': datetime(...),  # last modified time
    'accessed': datetime(...),  # last accessed time
    'should_delete': True,  # whether the file should be deleted
    'confidence': 0.85,  # confidence score (0-1)
    'reasons': ['Temporary file pattern', 'Old file'],  # reasons for deletion
    'model_used': True  # whether a trained model was used
}
```

## Customizing the Analyzer

You can extend the `MLFileAnalyzer` class to add custom rules:

```python
from file_cleanup.ml import MLFileAnalyzer

class CustomFileAnalyzer(MLFileAnalyzer):
    def _is_temp_file(self, file_info):
        """Override the default temp file detection."""
        path = Path(file_info['path'])
        return path.suffix.lower() in ['.tmp', '.temp', '.bak']

# Use the custom analyzer
analyzer = CustomFileAnalyzer()
results = analyzer.analyze_directory("/path/to/directory")
```
