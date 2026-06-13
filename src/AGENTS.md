# src directory

- root directory for the application components, 
    - `webapp/` for the django web application, which contains the REST API and the user interface
    - `ticketsystemmock/` for the standalone Python SDK that consumes the REST API for Python integration use cases
    - `n8n_node/` for the n8n custom node, which consumes the webapp REST API and exposes operations in n8n terms
- keep `ticketsystemmock/` self-contained and installable on its own; do not make it depend on `src/webapp` internals
- use the scripts under `scripts/ticketsystemmock/` for SDK compile, complexity, security, unittest, and coverage validation
