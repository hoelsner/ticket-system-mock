# AGENTS.md

## General Guidelines

- each main directory (`.devcontainer/`, `deploy/`, `docs/`, `src/`) contains an `AGENTS.md` file that defines directory specific guidelines and rules.
- these files are meant to be concise and actionable, providing clear guidance on how to structure and maintain the respective directory.
- they are not meant to be exhaustive, but rather to capture the most important principles and rules that should be followed when working with the code and assets in the respective directory and subdirectories
- read the UBIQUITOUS_LANGUAGE.md file to understand the domain and the terminology used in the project

## Repository Structure

- `.devcontainer/`: contains devcontainer configurations for local development environments
- `deploy/`: contains production deployment assets, e.g. Dockerfiles and compose templates
- `docs/`: contains relevant information and documentation for developers, architects, and users, e.g. markdown files, diagrams, etc.
- `src/`: root directory for the application components, e.g. the django webapp, the standalone Python SDK, and the n8n custom node
- `scripts/`: contains executable scripts for various tasks, e.g. cleaning directories, checking code complexity, etc.

## Working Guidelines

- Use `AGENTS.md` for directory-specific guidelines and rules.
- Use `SKILL.md` for reusable workflows and procedures.
- Use `scripts/` for executable scripts and automation.
- Use `docs/` for documentation and reference materials.
- general workflow
    1. Understand the problem and desired outcome
    2. Collect all relevant information and clarify any ambiguities with the user
    3. Break down the problem into smaller, manageable tasks
    4. Write clean, modular code that follows the project's style and guidelines
    5. Test your code thoroughly, including edge cases and error handling
    6. Document your code and any important decisions or assumptions

## Programming Guidelines

- the application is based on python 3.14
- `uv` is used as the package manager and to create virtual environments
