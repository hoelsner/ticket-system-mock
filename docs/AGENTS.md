# documentation directory

- directory for documentation related files, e.g. markdown files, diagrams, etc.
- directory for:
    - development documentation (`development/`), which contains information about development rules, processes, and guidelines
    - architecture documentation (`architecture/`), which contains architectural decision records, architectural diagrams, and other information related to the architecture of the application
    - external documentation (`external/`), which contains information about external dependencies and APIs, e.g. django, htmx, n8n etc.
    - user documentation (`user/`), that contains a user centric documentation for the web application that is shipped with the application

- all directories contain a mkdocs project, which can be used to build and serve the documentation locally. The mkdocs configuration is located in the respective directory.