#!/bin/bash
set -euo pipefail

echo "install uv..."
pip install uv

# create virtual environment and install dependencies
echo "installing dependencies..."

echo "creating virtual environment..."
uv venv --python 3.14 src/webapp/.venv --clear

echo "installing dependencies..."
source src/webapp/.venv/bin/activate
uv pip install --no-cache-dir --requirement src/webapp/requirements.txt --prefix src/webapp/.venv
uv pip install --no-cache-dir --requirement .devcontainer/requirements.txt --prefix src/webapp/.venv

echo "customizing shell..."

echo "DONE"
echo ""
