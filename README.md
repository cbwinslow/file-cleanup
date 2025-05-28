# 🧹 File Cleanup Utility

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/yourusername/file-cleanup-utility/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/file-cleanup-utility/actions)
[![codecov](https://codecov.io/gh/yourusername/file-cleanup-utility/branch/main/graph/badge.svg?token=YOUR-TOKEN)](https://codecov.io/gh/yourusername/file-cleanup-utility)
[![PyPI version](https://badge.fury.io/py/file-cleanup-utility.svg)](https://badge.fury.io/py/file-cleanup-utility)

A powerful, extensible command-line utility for analyzing, organizing, and cleaning up your file system. Built with Python and designed for developers, system administrators, and power users.

## ✨ Features

- **Smart File Analysis**
  - 🕵️ Detect duplicate files using content hashing
  - 📅 Find old and unused files
  - 🔍 Identify similar files using advanced algorithms
  - 🗑️ Discover deprecated and temporary files
  - 🔗 Find broken symlinks and orphaned files

- **Advanced Processing**
  - 🧩 Extensible plugin system
  - 📊 Detailed reporting and statistics
  - 🔄 Batch processing for large directories
  - 🛡️ Safe operations with dry-run mode
  - ⚡ Multi-threaded operations for better performance

- **Rich Output**
  - 🎨 Colorful terminal output with rich
  - 📝 Generate reports in multiple formats (JSON, CSV, table)
  - 📈 Visual statistics and progress bars
  - 🔍 Interactive mode for reviewing changes

## 🚀 Installation

### Using pip (recommended)

```bash
pip install file-cleanup-utility
```

### From source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/file-cleanup-utility.git
   cd file-cleanup-utility
   ```

2. Install with pip in development mode:
   ```bash
   pip install -e .[dev]
   ```

### Using Docker

```bash
docker run -v $(pwd):/data ghcr.io/yourusername/file-cleanup:latest scan /data
```

## 🛠️ Usage

### Basic Commands

```bash
# Scan a directory
file-cleanup scan /path/to/directory

# Analyze files (find duplicates, old files, etc.)
file-cleanup analyze /path/to/directory

# Clean up files (with dry run)
file-cleanup clean /path/to/directory --dry-run

# Find duplicate files
file-cleanup duplicates /path/to/directory

# Generate a detailed report
file-cleanup report /path/to/directory --format=json
```

### Advanced Usage

```bash
# Find files older than 90 days
file-cleanup analyze /path --age-days=90

# Use a higher similarity threshold (0.95)
file-cleanup analyze /path --similarity=0.95

# Clean files interactively
file-cleanup clean /path --confirm

# Generate a CSV report
file-cleanup report /path --format=csv --output=report.csv
```

## 📊 Example Output

### Scan Command
```
📂 Scanning directory: /home/user/documents

🔍 Found 1,234 files (1.2 GB)
⏱️  Scan completed in 2.3s

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Metric                     ┃ Value           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ Total Files                │ 1,234           │
│ Total Size                 │ 1.2 GB          │
│ Average File Size          │ 1.0 MB          │
│ Largest File               │ 45.6 MB         │
│ Oldest File (days)         │ 1,245           │
│ Newest File (days)         │ 0               │
└────────────────────────────┴──────────────────┘
```

## 🧩 Plugins

Extend functionality with plugins:

1. **Image Analysis** - Find similar images
2. **Document Analysis** - Extract text and metadata
3. **Media Analysis** - Analyze audio/video files
4. **Cloud Storage** - Connect to cloud providers

## ⚙️ Configuration

Create a `config.toml` in your home directory (`~/.config/file-cleanup/config.toml`):

```toml
[general]
default_age_days = 90
similarity_threshold = 0.85
max_file_size = "10GB"

[paths]
exclude = ["**/node_modules/**", "**/.git/**"]
include = ["**/*.py", "**/*.md"]

[cleanup]
move_to_trash = true
backup_before_delete = true
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

For full documentation, visit [https://yourusername.github.io/file-cleanup-utility](https://yourusername.github.io/file-cleanup-utility)

## 📬 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - your.email@example.com

Project Link: [https://github.com/yourusername/file-cleanup-utility](https://github.com/yourusername/file-cleanup-utility)
