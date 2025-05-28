#!/usr/bin/env python3
"""
This is a convenience script to run tests.
It's equivalent to running `python -m pytest` from the command line.
"""

import sys
import pytest

if __name__ == "__main__":
    # Exit with the test status code
    sys.exit(pytest.main(sys.argv[1:]))
