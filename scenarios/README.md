# Scenarios

Use the scenario packages in this directory to reset a Ticket System Mock
instance and seed a ready-to-demo setup.

## Before You Start

1. Open a terminal in the repository root.
2. Create or refresh the dedicated scenarios environment:

	```bash
	cd scenarios
	uv sync --python 3.14
	cd ..
	```

3. Make sure the Ticket System Mock instance you want to seed is running.
4. Make sure you know the credentials for a superuser account in that instance.

## How To Use A Scenario

1. Open the scenario directory you want to run.
2. Read that scenario's `README.md` for the exact setup and outcome.
3. Run the scenario's `seed.py` script with the Python interpreter from
	`scenarios/.venv`.
4. Confirm the destructive reset when prompted.

Each scenario resets the target instance before seeding its own data. Run a
scenario only against an instance you are prepared to clear.

## Available Scenario Layout

Each scenario directory includes:

- `README.md` with the user steps for that scenario
- `seed.py` to reset and seed the instance
- `assets/` for supporting files such as workflow exports

## Current Scenario

- `issue-triage-with-n8n`: prepares a triage-focused demo instance and pairs
  with an n8n workflow asset