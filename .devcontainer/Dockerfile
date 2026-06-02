# dockerfile for the devcontainer setups
FROM mcr.microsoft.com/devcontainers/python:1-3.13

# build parameters
ARG UID=1000
ARG GID=1000
ARG REQUIREMENTS_FILE="requirements.txt"
ARG BUILD_VERSION="undefined"
ARG COMMIT_ID="undefined"
ENV PATH="${PATH}:/home/vscode/.local/bin"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN set -eux; \
    CODENAME="$(awk -F= '/^VERSION_CODENAME=/{print $2}' /etc/os-release)"; \
    apt-get install -y gnupg2 lsb-release wget ca-certificates \
    && wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/keyrings/postgres.gpg \
    && chmod 0644 /etc/apt/keyrings/postgres.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/postgres.gpg] https://apt.postgresql.org/pub/repos/apt ${CODENAME}-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list \
    && rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update -y \
    # postgres-client-15 is not available in the base image, required for backup
    && apt-get install -y --no-install-recommends nano iputils-ping dnsutils gettext-base postgresql-client-15 ripgrep \
    && apt-get install -y --no-install-recommends libldap2-dev python3-dev libsasl2-dev python3-ldap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD --chown=vscode:vscode .devcontainer/requirements* /tmp/pip/
RUN python -m pip install --no-cache-dir --upgrade pip uv \
    && uv pip install --system --no-cache -r /tmp/pip/$REQUIREMENTS_FILE

USER vscode
WORKDIR /workspaces
