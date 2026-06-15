# src directory

- root directory for the application components, 
    - `webapp/` for the django web application, which contains the REST API and the user interface
    - `ticketsystemmock/` for the standalone Python SDK that consumes the REST API for Python integration use cases
    - `n8n_node/` for the n8n custom node, which consumes the webapp REST API and exposes operations in n8n terms
- keep `ticketsystemmock/` self-contained and installable on its own; do not make it depend on `src/webapp` internals
- keep the SDK Python environment separate in `src/ticketsystemmock/.venv` and manage it with `uv` using Python 3.14
- use the scripts under `scripts/ticketsystemmock/` for SDK compile, complexity, security, unittest, and coverage validation
- use the scripts under `scripts/n8n_node/` for n8n node build, typecheck, lint or complexity, unittest, audit, and package validation instead of ad hoc commands when verifying repository work
- keep n8n node request builders and operation helpers small enough to satisfy the repository complexity checks; when a function starts accumulating many conditional branches, extract focused helpers instead of extending the same function further
