#!/bin/sh

export TABLE_NAME="test_table"

coverage run -m pytest tests
coverage report --omit="*/__init__.py,tests/*" 