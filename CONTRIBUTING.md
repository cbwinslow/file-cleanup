# Contributing to File Cleanup Utility

🎉 First off, thanks for taking the time to contribute! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/yourusername/file-cleanup-utility.git
   cd file-cleanup-utility
   ```
3. **Set up the development environment** (see below)
4. **Create a feature branch** for your changes
   ```bash
   git checkout -b feature/amazing-feature
   ```

## Development Setup

1. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -e .[dev]
   pre-commit install
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Run tests** to verify your setup
   ```bash
   pytest
   ```

## Making Changes

1. **Make your changes** following the code style guide
2. **Add tests** for new functionality
3. **Update documentation** as needed
4. **Run tests** to ensure nothing is broken
   ```bash
   pytest
   ```
5. **Run linters and formatters**
   ```bash
   black .
   isort .
   flake8
   mypy .
   ```
6. **Commit your changes** with a descriptive message
   ```bash
   git commit -m "Add amazing new feature"
   ```

## Code Style

We use several tools to maintain code quality and style:

- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **Mypy** for static type checking
- **Pre-commit hooks** to run these automatically

To automatically format your code:
```bash
black .
isort .
```

## Testing

We use `pytest` for testing. To run tests:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=file_cleanup --cov-report=term-missing

# Run a specific test file
pytest tests/test_analyzer.py

# Run tests in parallel
pytest -n auto
```

## Documentation

We use Sphinx for documentation. To build the docs:

```bash
# Install docs dependencies
pip install -e .[docs]

# Build the docs
cd docs
make html

# View the docs
open _build/html/index.html
```

## Submitting a Pull Request

1. **Push your changes** to your fork
   ```bash
   git push origin feature/amazing-feature
   ```
2. **Open a Pull Request** from your fork to the main repository
3. **Describe your changes** in the PR description:
   - What problem does this solve?
   - What approach did you take?
   - Any breaking changes?
   - Any additional context?
4. **Wait for CI** to run all tests
5. **Address any feedback** from code review

## Reporting Bugs

Found a bug? Please open an issue with:

1. A clear title and description
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Environment details (OS, Python version, etc.)
5. Any relevant logs or screenshots

## Feature Requests

Have an idea for a new feature? Open an issue with:

1. A clear description of the feature
2. The problem it solves
3. Any alternatives you've considered
4. Additional context or examples

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

Thank you for contributing to File Cleanup Utility! Your help is greatly appreciated. 💙
