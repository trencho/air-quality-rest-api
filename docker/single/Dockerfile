FROM ubuntu

LABEL maintainer="Aleksandar Trenchevski <atrenchevski@gmail.com>"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y python3-pip python3-dev nginx tzdata && \
    apt-get autoclean clean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    chmod 777 /run -R && \
    chmod 777 /root -R

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container
COPY . .
COPY ./docker/nginx.conf /etc/nginx/nginx.conf

# Install the dependencies
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements/prod.txt

# Define the required user ids and name
ARG USER_ID=1000
ENV USER_ID=$USER_ID

ARG USER_GID=1000
ENV USER_GID=$USER_GID

ARG USER_NAME=flask

RUN addgroup --gid $USER_GID $USER_NAME && \
    adduser --disabled-password --gecos "" --uid $USER_ID --gid $USER_GID $USER_NAME

# Set ownership and permissions for the app and var folder
RUN chown -R $USER_NAME:$USER_NAME /app && \
    chown -R $USER_NAME:$USER_NAME /var/lib/nginx && \
    chown -R $USER_NAME:$USER_NAME /var/log/nginx && \
    chmod -R 755 /app

# Set the user for subsequent instructions
USER $USER_NAME

EXPOSE 80

# Run the command to start nginx + gunicorn
ENTRYPOINT ["/bin/bash", "/app/docker/single/launch.sh"]