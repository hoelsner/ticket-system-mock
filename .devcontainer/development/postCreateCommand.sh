#!/bin/bash
set -euo pipefail

echo "install uv..."
pip install uv

# create virtual environment and install dependencies
echo "installing dependencies..."

echo "creating virtual environment..."
uv venv --python 3.14 src/webapp/.venv --clear

echo "creating Ticket System Mock SDK virtual environment..."
pushd src/ticketsystemmock >/dev/null
uv sync --python 3.14
popd >/dev/null

echo "creating scenarios virtual environment..."
pushd scenarios >/dev/null
uv sync --python 3.14
popd >/dev/null

echo "installing dependencies..."
source src/webapp/.venv/bin/activate
uv pip install --no-cache-dir --requirement src/webapp/requirements.txt --prefix src/webapp/.venv
uv pip install --no-cache-dir --requirement .devcontainer/requirements.txt --prefix src/webapp/.venv

echo "install npx dependencies..."
npx -g -y playwright install
npx -g -y playwright install-deps
npx -y @playwright/mcp install-browser chrome-for-testing

echo "customizing shell..."
pre-commit install

echo "DONE"
echo ""
