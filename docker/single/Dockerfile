FROM ubuntu

LABEL maintainer="Aleksandar Trenchevski <atrenchevski@gmail.com>"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y python3-pip python3-dev nginx tzdata && \
    apt-get autoclean clean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set the working directory to /app
WORKDIR /app

COPY requirements .
# Install the dependencies
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements/prod.txt

# Copy the current directory contents into the container
COPY . .
COPY ./docker/nginx.conf /etc/nginx/nginx.conf



# Set ownership and permissions for the app and var folder
RUN adduser --disabled-password --gecos '' nginx && \
    chown -R nginx:nginx /app && \
    chmod 777 /run -R && \
    chmod 777 /root -R

# Set the user for subsequent instructions
USER nginx

EXPOSE 80

# Run the command to start nginx + gunicorn
ENTRYPOINT ["/bin/bash", "/app/docker/single/launch.sh"]