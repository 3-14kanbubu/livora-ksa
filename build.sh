#!/bin/bash
# Build script for Render

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

cd website
python manage.py collectstatic --no-input
python manage.py migrate
