# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

FROM python:3.13.3-slim

LABEL maintainer="Aleksandar Trenchevski <atrenchevski@gmail.com>"

# Prevents Python from writing pyc files and keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies.
RUN apt update && \
    apt upgrade -y && \
    apt dist-upgrade -y && \
    apt install -y --no-install-recommends libgomp1 nginx tzdata && \
    apt autoclean clean && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements,target=requirements \
    pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements/prod.txt

# Copy the source code into the container.
COPY . .

# Copy the nginx configuration file.
COPY ./docker/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Run the application.
ENTRYPOINT ["/bin/bash", "/app/docker/launch.sh"]