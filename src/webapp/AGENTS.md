# Django Web Application for Ticketing Demo Service

## Environment and Configuration

- the webapp uses a virtual environment located at `.venv` in this directory
- the application follows the 12factor app
- all configurations are provided through environment variables, useful defaults are defined within the application settings
- install the dependencies with `uv pip install -r requirements.txt` within the virtual environment

## Application Appearance and Behavior

- the application name `IT Operation Ticketing Demo Service` is within the webapplication
- the user frontend and the admin frontend must both support a light mode and a dark mode
- the entire application must support multiple languages using Django's built-in i18n approach
- the login or sign-up page must use a split layout with a functional left panel and a contextual right-side product illustration
- the authenticated application must use a top-down shell with a persistent top navigation bar, a left burger menu for collapsible detailed navigation, a top-right utility area, and a main content area for page-specific workflows
- when building or restyling frontend screens, keep the repository layout rules authoritative and use the `frontend-design` skill for deliberate visual direction instead of defaulting to generic layouts
- visual tone must come from palette, typography, structure, and texture, not from fabricated issue data, filler labels, or themed replacements for standard UI copy

## Database and Migrations

- you must create a migration always using the command `python3 manage.py makemigrations` and then apply the migration with `python3 manage.py migrate`

## Django

- all django apps should be created within the `src/webapp/djangoapp` directory, you can create subdirectories to organize your apps if needed
- the templates are located in the `src/webapp/templates` directory, you create a subdirectory that matches the app name for each view within the corresponding app directory, you can create subdirectories to organize your templates if needed
- the static files are located in the `src/webapp/static` directory, you can create subdirectories to organize your static files if needed
- keep domain entities and business logic in `djangoapp.core`
- keep machine-facing REST API endpoints and URL wiring in `djangoapp.rest_api`
- keep authenticated HTML views and UI URL wiring in `djangoapp.user_interface`
- `djangoapp.rest_api` and `djangoapp.user_interface` may depend on `djangoapp.core`, but `djangoapp.core` should not depend on either surface app
- implement entity-specific business logic through controller classes in Python instead of placing it directly in Django views, forms, signals, or REST API views
- when a domain area in `djangoapp.core` grows beyond a small single-file implementation, split it into a package and keep one class per file for models and controllers
- preserve stable package-level imports for Django integration points such as admin modules, signals, tests, and migrations by re-exporting public classes from the package `__init__.py`
- use the following structural flow for the user frontend: view -> controller -> model
- use the following structural flow for form handling in the user frontend: view -> form -> controller -> model
- use the following structural flow for model event handling: signal -> controller
- use the following structural flow for the REST API: REST API view -> controller -> model
- use Django's built-in internationalization support for multilingual features, including `LocaleMiddleware`, translation tags, and message catalogs
- design the user and admin frontends so both light mode and dark mode are supported as first-class UI requirements
- keep controllers focused on business rules per entity and use models for persistence and Django-native validation
- for model packages, keep shared helpers such as enums and upload-path functions in dedicated files inside the same package instead of recreating monolithic modules

## Dependency Management

- do not add any dependencies to the project without confirmation, if you think a dependency is needed, mention it first and wait for confirmation before adding it to the project.
- the project uses `uv` for dependency management
- use the `add-webapp-python-dependency` skill to add a new dependency to the webapp, this will ensure that the dependency is added correctly and consistently with the project rules

## Static file handling

- all static files should be placed in the `src/webapp/static` directory, you can create subdirectories to organize your static files if needed
- do not use any cdn for static files, all static files should be served from the application itself
- download the static files and place them in the `src/webapp/static` directory using the `fetch_static_files.bash` script located in the `scripts` directory, you can run the script with `bash scripts/fetch_static_files.bash`
- for frontend enhancements, prefer semantic HTML, Pico CSS primitives and variables, Django Cotton components, HTMX, and data attributes before introducing heavier custom structure or scripting

## Unit Testing

- create the test cases within the `tests` directory, use module names matching `tests_*.py`, and create subdirectories only when needed
- keep tests inside an internal app-local `tests/` package with an `__init__.py` marker; do not expose tests through the app package `__init__.py` or any other public API surface
- use the python `unittest` framework for writing your tests, you can refer to the official documentation for more information: https://docs.python.org/3/library/unittest.html
- use the repository test scripts or run `python3 manage.py test <app>.tests` so Django loads the internal tests packages explicitly; do not rely on importing tests from the app package

## Development Server

- you have a running version of the application available at `http://webapp:8000` when running the development server
- you can restart the development server with `make webapp-restart-devserver` command, this will restart the webapp service in the docker compose setup
- to verify that the development server is working, use the command `docker compose logs webapp` to check the logs for any errors or issues, you should see a message indicating that the server is running and listening on port 8000, use this also to troubleshoot wrong behavior