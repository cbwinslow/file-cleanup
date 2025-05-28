.PHONY: help install install-dev install-test install-docs clean clean-build clean-pyc clean-test lint test test-all coverage docs servedocs release dist check-release install-twine

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs/source
BUILDDIR      = docs/build

# Help target
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  install         install the package in development mode"
	@echo "  install-dev     install development dependencies"
	@echo "  install-test    install test dependencies"
	@echo "  install-docs    install documentation dependencies"
	@echo "  clean           remove all build, test, coverage and Python artifacts"
	@echo "  clean-build     remove build artifacts"
	@echo "  clean-pyc       remove Python file artifacts"
	@echo "  clean-test      remove test and coverage artifacts"
	@echo "  lint            check style with flake8 and isort"
	@echo "  test            run tests quickly with the default Python"
	@echo "  test-all        run tests on every Python version with tox"
	@echo "  coverage        check code coverage quickly with the default Python"
	@echo "  docs            generate Sphinx HTML documentation, including API docs"
	@echo "  servedocs       compile the docs watching for changes"
	@echo "  release         package and upload a release"
	@echo "  dist            package"
	@echo "  check-release   check distribution files before release"

# Install targets
install: clean-build
	pip install -e .


install-dev:
	pip install -r requirements-dev.txt

install-test:
	pip install pytest pytest-cov pytest-mock pytest-xdist

install-docs:
	pip install -r docs/requirements.txt

# Clean targets
clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr .mypy_cache
	rm -fr .ruff_cache

# Lint and test targets
lint:
	black --check .
	isort --check-only .
	flake8 file_cleanup tests
	mypy file_cleanup
	ruff check .


format:
	black .
	isort .
	ruff check --fix .

test:
	pytest -v --cov=file_cleanup --cov-report=term-missing

test-all:
	tox

coverage:
	coverage run --source file_cleanup -m pytest
	coverage report -m
	coverage html
	@echo "Opening HTML coverage report..."
	@python -c "import webbrowser; webbrowser.open('htmlcov/index.html')"

# Documentation targets
docs:
	rm -f docs/file_cleanup.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ file_cleanup
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "The HTML pages are in $(BUILDDIR)/html."

servedocs:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "View the docs at http://localhost:8000"
	python -m http.server --directory "$(BUILDDIR)/html" 8000

# Release targets
release: clean dist check-release
	twine upload dist/*

dist: clean
	python -m build
	ls -l dist

check-release: dist
	twine check dist/*

# Install twine for release
install-twine:
	pip install --upgrade twine

# Install pre-commit hooks
install-pre-commit:
	pre-commit install

# Run pre-commit on all files
pre-commit-all:
	pre-commit run --all-files

# Run pre-commit on staged files only
pre-commit:
	pre-commit run

# Run tests with coverage and open the report
cov:
	pytest --cov=file_cleanup --cov-report=html
	python -m webbrowser -t htmlcov/index.html

# Run tests with coverage and fail under threshold
cov-fail-under:
	pytest --cov=file_cleanup --cov-fail-under=90

# Run tests with coverage and generate XML for CI
cov-xml:
	pytest --cov=file_cleanup --cov-report=xml:coverage.xml

# Run tests with coverage and generate Cobertura XML for CI
cov-cobertura:
	pytest --cov=file_cleanup --cov-report=xml:coverage.xml --cov-report=term-missing

# Run tests with coverage and generate HTML report
cov-html:
	pytest --cov=file_cleanup --cov-report=html

# Run tests with coverage and generate a term report
cov-term:
	pytest --cov=file_cleanup --cov-report=term-missing

# Run tests with coverage and generate all reports
cov-all:
	pytest --cov=file_cleanup --cov-report=html --cov-report=xml:coverage.xml --cov-report=term-missing

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-90:
	pytest --cov=file_cleanup --cov-fail-under=90

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-80:
	pytest --cov=file_cleanup --cov-fail-under=80

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-70:
	pytest --cov=file_cleanup --cov-fail-under=70

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-60:
	pytest --cov=file_cleanup --cov-fail-under=60

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-50:
	pytest --cov=file_cleanup --cov-fail-under=50

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-40:
	pytest --cov=file_cleanup --cov-fail-under=40

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-30:
	pytest --cov=file_cleanup --cov-fail-under=30

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-20:
	pytest --cov=file_cleanup --cov-fail-under=20

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-10:
	pytest --cov=file_cleanup --cov-fail-under=10

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-0:
	pytest --cov=file_cleanup --cov-fail-under=0

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-100:
	pytest --cov=file_cleanup --cov-fail-under=100

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-95:
	pytest --cov=file_cleanup --cov-fail-under=95

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-85:
	pytest --cov=file_cleanup --cov-fail-under=85

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-75:
	pytest --cov=file_cleanup --cov-fail-under=75

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-65:
	pytest --cov=file_cleanup --cov-fail-under=65

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-55:
	pytest --cov=file_cleanup --cov-fail-under=55

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-45:
	pytest --cov=file_cleanup --cov-fail-under=45

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-35:
	pytest --cov=file_cleanup --cov-fail-under=35

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-25:
	pytest --cov=file_cleanup --cov-fail-under=25

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-15:
	pytest --cov=file_cleanup --cov-fail-under=15

# Run tests with coverage and fail if coverage is below threshold
cov-fail-under-5:
	pytest --cov=file_cleanup --cov-fail-under=5
