# Deployment directory

## Guidelines

- the deployment should follow the 12factor app and all configurations should be provided via environment variables or a .env file

## Structure

- directory for deployment related files, e.g. Dockerfiles, Scripts shipped with the application
- `containers`: Dockerfiles and related scripts for building and running containers for the web application. Each subdirectory corresponds to a container, e.g. `webapp` for the web application container
- `docker-compose`: Docker Compose files for orchestrating multi-container deployments, e.g. `docker-compose.yaml` for production deployments that starts a full stack of containers (webapp, database, etc.)
- `build_scripts`: scripts for building and packaging the application to deploy the containers using docker-compose

## Production deployment

- the docker-compose files (`docker-compose.yaml` and `docker-compose.override.yaml`) are copied to the root of the repository and can be used to start the application in production with `docker compose -f docker-compose.yaml up`
