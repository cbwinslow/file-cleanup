from setuptools import setup, find_packages
import pathlib
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# Read the contents of README.md
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

# Version extraction inspired from 'requests' setup.py
HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

def get_version() -> str:
    """Extract version from the package's __init__.py file."""
    version_file = os.path.join(HERE, "src", "file_cleanup", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        version_match = re.search(
            r'^__version__ = ["\']([^"\']+)["\']', f.read(), re.MULTILINE
        )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def parse_requirements_file(filename: str) -> List[str]:
    """Parse a requirements file and return a list of requirements."""
    with open(os.path.join(HERE, filename), encoding="utf-8") as f:
        requirements = []
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Remove inline comments
            if "#" in line:
                line = line[: line.find("#")].strip()
            requirements.append(line)
        return requirements

# Get requirements from requirements.txt
INSTALL_REQUIRES = parse_requirements_file("requirements.txt")

# Development dependencies
EXTRAS_REQUIRE: Dict[str, List[str]] = {
    "dev": parse_requirements_file("requirements-dev.txt"),
}

# Add all extra requirements as 'all' extra
EXTRAS_REQUIRE["all"] = list(
    {req for reqs in EXTRAS_REQUIRE.values() for req in reqs}
)

# Get the version
VERSION = get_version()

# Package configuration
setup(
    name="file-cleanup-utility",
    version=VERSION,
    description="A powerful file system cleanup and analysis tool",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Blaine Winslow",
    author_email="blaine.winslow@gmail.com",
    url="https://github.com/cbwinslow/file-cleanup-utility",
    project_urls={
        "Bug Reports": "https://github.com/cbwinslow/file-cleanup-utility/issues",
        "Source": "https://github.com/cbwinslow/file-cleanup-utility",
        "Documentation": "https://github.com/cbwinslow/file-cleanup-utility#readme",
        "Changelog": "https://github.com/cbwinslow/file-cleanup-utility/blob/main/CHANGELOG.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "file_cleanup": ["py.typed"],
    },
    include_package_data=True,
    python_requires=">=3.8, <4",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        "console_scripts": [
            "file-cleanup=file_cleanup.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: System :: Filesystems",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    keywords=[
        "file",
        "cleanup",
        "duplicates",
        "organization",
        "cli",
        "utility",
    ],
    zip_safe=False,
    license="MIT",
    license_files=("LICENSE",),
)

if __name__ == "__main__":
    setup(
        project_urls={
            "Bug Reports": "https://github.com/cbwinslow/file-cleanup-utility/issues",
            "Source": "https://github.com/cbwinslow/file-cleanup-utility",
        },
    )
