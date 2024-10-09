FROM python:3.12-slim

LABEL maintainer="Aleksandar Trenchevski <atrenchevski@gmail.com>"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt upgrade -y && \
    apt dist-upgrade -y && \
    apt install -y --no-install-recommends libgomp1 nginx tzdata && \
    apt autoclean clean && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set the working directory to /app
WORKDIR /app

# Install the dependencies
COPY requirements ./requirements
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements/prod.txt

# Copy the current directory contents into the container
COPY . .
COPY ./docker/nginx.conf /etc/nginx/nginx.conf

# Set ownership and permissions for the system folders
RUN adduser --disabled-password --gecos '' nginx && \
    chown -R nginx:nginx /app && \
    chmod -R o+rX /app && \
    chmod 777 /run

EXPOSE 80

# Run the command to start nginx + gunicorn
ENTRYPOINT ["/bin/bash", "/app/docker/single/launch.sh"]