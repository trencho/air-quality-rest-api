FROM ubuntu:latest

LABEL maintainer='Aleksandar Trenchevski <atrenchevski@gmail.com>'

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y python3-pip python3-dev && \
    apt-get install -y nginx uwsgi uwsgi-plugin-python3 && \
    apt-get install -y tzdata && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./requirements.txt /requirements.txt
COPY ./docker/single/nginx.conf /etc/nginx/nginx.conf

WORKDIR /

# Install the dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . /

RUN adduser --disabled-password --gecos '' nginx && \
    chown -R nginx:nginx /src && \
    chmod 777 /run/ -R && \
    chmod 777 /root/ -R

# Run the command to start nginx + uWSGI
ENTRYPOINT ["/bin/bash", "/docker/single/launch.sh"]