FROM python:latest

LABEL maintainer='Aleksandar Trenchevski <atrenchevski@gmail.com>'

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y uwsgi uwsgi-plugin-python3 && \
    apt-get install -y tzdata && \
    apt-get autoclean clean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./requirements.txt /requirements.txt

WORKDIR /

# Install the dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . /

RUN chmod 777 /run/ -R && \
    chmod 777 /root/ -R

# Run the command to start uWSGI
ENTRYPOINT ["uwsgi", "--ini", "/docker/multi/flask/uwsgi.ini"]