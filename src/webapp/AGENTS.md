# Django Web Application for Ticketing Demo Service

## Environment and Configuration

- the webapp uses a virtual environment located at `.venv` in this directory
- the application follows the 12factor app
- all configurations are provided through environment variables, useful defaults are defined within the application settings
- install the dependencies with `uv pip install -r requirements.txt` within the virtual environment

## Application Appearance and Behavior

- the application name `IT Operation Ticketing Demo Service` is within the webapplication

## Database and Migrations

- you must create a migration always using the command `python3 manage.py makemigrations` and then apply the migration with `python3 manage.py migrate`

## Django

- all django apps should be created within the `src/webapp/djangoapp` directory, you can create subdirectories to organize your apps if needed
- the templates are located in the `src/webapp/templates` directory, you create a subdirectory that matches the app name for each view within the corresponding app directory, you can create subdirectories to organize your templates if needed
- the static files are located in the `src/webapp/static` directory, you can create subdirectories to organize your static files if needed
- 

## Dependency Management

- do not add any dependencies to the project without confirmation, if you think a dependency is needed, mention it first and wait for confirmation before adding it to the project.
- the project uses `uv` for dependency management
- use the `add-webapp-python-dependency` skill to add a new dependency to the webapp, this will ensure that the dependency is added correctly and consistently with the project rules

## Static file handling

- all static files should be placed in the `src/webapp/static` directory, you can create subdirectories to organize your static files if needed
- do not use any cdn for static files, all static files should be served from the application itself
- download the static files and place them in the `src/webapp/static` directory using the `fetch_static_files.bash` script located in the `scripts` directory, you can run the script with `bash scripts/fetch_static_files.bash`

## Unit Testing

- create the test cases within the `tests` directory, you can create subdirectories to organize your tests if needed
- use the python `unittest` framework for writing your tests, you can refer to the official documentation for more information: https://docs.python.org/3/library/unittest.html
- use `python3 manage.py test` to run the unit tests, make sure to cover edge cases and error handling in your tests

## Development Server

- you have a running version of the application available at `http://webapp:8000` when running the development server
- you can restart the development server with `make webapp-restart-devserver` command, this will restart the webapp service in the docker compose setup
