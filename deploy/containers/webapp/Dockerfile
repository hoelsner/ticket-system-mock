FROM node:20-bookworm-slim AS n8n_node_builder

WORKDIR /app/src/n8n_node

COPY src/n8n_node/package*.json ./
RUN npm ci

COPY src/n8n_node ./
RUN npm run pack:node \
    && mkdir -p /tmp/n8n-node-package \
    && cp build/*.tgz /tmp/n8n-node-package/


FROM python:3.14-slim AS python_sdk_builder

WORKDIR /app/src/ticketsystemmock

RUN python -m pip install --upgrade pip uv

COPY src/ticketsystemmock /app/src/ticketsystemmock

RUN uv build --sdist /app/src/ticketsystemmock -o /tmp/python-sdk-package --clear --no-build-logs


FROM python:3.14-slim

ARG UID=1000
ARG GID=1000
ARG REQUIREMENTS_FILE="requirements.txt"
ARG COMMIT_ID="undefined"
ARG BUILD_VERSION="undefined"

ENV PATH="${PATH}:/home/appuser/.local/bin"
ENV PYTHONUNBUFFERED=1
ENV APP_ROOT="/app"
ENV DJANGO_SETTINGS_MODULE="djangoapp.settings"
ENV DJANGO_DEBUG="False"
ENV DJANGO_ALLOWED_HOSTS="*"
ENV DJANGO_TIME_ZONE="UTC"
ENV DJANGO_LOG_LEVEL="INFO"
ENV SERVICE_BASE_URL="http://localhost"
ENV PRODUCT_DISPLAY_NAME="Ticket System Mock"
ENV DJANGO_RUNTIME_ROOT="/runtime"
ENV DJANGO_STATIC_ROOT="/runtime/static"
ENV DJANGO_MEDIA_ROOT="/runtime/media"
ENV DJANGO_CERT_ROOT="/runtime/certificates"
ENV DJANGO_PROVISIONING_DIR="/runtime/provisioning"
ENV DJANGO_PROVISIONING_FLAG="/runtime/provisioning/fixtures-loaded.flag"
ENV DJANGO_BOOTSTRAP_FIXTURES="initial_data"
ENV DJANGO_STATIC_FIXTURES="static_data"
ENV POSTGRES_DB="itoticketing"
ENV POSTGRES_USER="itoticketing"
ENV POSTGRES_HOST="database"
ENV POSTGRES_PORT="5432"
ENV CACHE_HOST="cache"
ENV CACHE_PORT="6379"
ENV CACHE_DB="0"
ENV NGINX_SERVER_NAME="_"
ENV NGINX_CLIENT_MAX_BODY_SIZE="10m"
ENV GUNICORN_BIND_HOST="0.0.0.0"
ENV GUNICORN_BIND_PORT="8000"
ENV GUNICORN_WORKERS="2"
ENV GUNICORN_THREADS="2"
ENV GUNICORN_TIMEOUT="60"
ENV GUNICORN_GRACEFUL_TIMEOUT="30"
ENV GUNICORN_KEEPALIVE="5"
ENV GUNICORN_LOG_LEVEL="info"
ENV APP_BUILD_VERSION="$BUILD_VERSION"
ENV APP_BUILD_COMMIT_ID="$COMMIT_ID"

RUN groupadd -g "${GID}" appuser \
    && useradd -l -u "${UID}" -g appuser -ms /bin/bash appuser

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --chown=appuser:appuser src/webapp/requirements* /tmp/pip/

RUN python -m pip install --upgrade pip uv \
    && uv pip install --system --no-cache -r "/tmp/pip/${REQUIREMENTS_FILE}"

COPY --chown=appuser:appuser deploy/containers/webapp/*.bash /app/deploy/containers/webapp/
COPY scripts/fetch_static_files.bash /tmp/fetch_static_files.bash
COPY --chown=appuser:appuser src/webapp /app/src/webapp
COPY --chown=appuser:appuser docs/user /app/docs/user
COPY --from=n8n_node_builder /tmp/n8n-node-package /app/build/integrations
COPY --from=python_sdk_builder /tmp/python-sdk-package /app/build/integrations

RUN REPO_ROOT=/app bash /tmp/fetch_static_files.bash \
    && mkdir -p /app/build /runtime/static /runtime/media /runtime/certificates /runtime/provisioning /runtime/nginx \
    && printf '%s\n' "$BUILD_VERSION" > /app/build/image-version.txt \
    && printf '%s\n' "$COMMIT_ID" > /app/build/image-commit.txt \
    && rm -f /tmp/fetch_static_files.bash \
    && chown -R appuser:appuser /app /runtime

LABEL org.opencontainers.image.title="Ticket System Mock" \
      org.opencontainers.image.version="$BUILD_VERSION" \
      org.opencontainers.image.revision="$COMMIT_ID"

USER appuser
WORKDIR /app

CMD ["/bin/bash", "/app/deploy/containers/webapp/run_webapp.bash"]
