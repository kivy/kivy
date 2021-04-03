#!/bin/bash
# Print test output
pytest --cov-report term-missing --cov=kivy kivy/tests/
# Print test output and save to html. To view, open `htmlcov/index.html`.
# pytest --cov-report html --cov-report term-missing --cov=kivy kivy/tests/