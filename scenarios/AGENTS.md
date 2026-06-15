# scenarios directory

- each scenario must stay standalone inside its own subdirectory
- each scenario directory should contain a `README.md`, one seeding script, and an `assets/` directory
- scenario scripts may depend only on the standalone `ticketsystemmock` Python SDK and the Python standard library unless the user explicitly asks for more
- use the dedicated Python 3.14 virtual environment in `scenarios/.venv`
- manage the scenarios environment with `uv`, for example `uv sync --python 3.14` from this directory