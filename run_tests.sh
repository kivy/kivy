#!/bin/bash
# =================
# Run Kivy Tests
# =================
# When running tests, we have 3 useful options. Comment and uncomment as
# desired.

# 1. Print test output
pytest --cov-report term-missing --cov=kivy kivy/tests/

# 2. Save test output to html. To view, run the below and open
#    `htmlcov/index.html`.
# Note: This option does not currently include the missing lines analysis.
# pytest --cov-report html --cov-report term-missing --cov=kivy kivy/tests/

# 3. Print test output and save to 'coverage.txt'
# pytest --cov-report term-missing --cov=kivy kivy/tests/ > coverage.txt
