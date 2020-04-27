FROM ubuntu:19.10

MAINTAINER Aleksandar Trenchevski <atrenchevski@gmail.com>

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev && \
    apt-get install -y uwsgi uwsgi-plugin-python3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./requirements.txt /requirements.txt

WORKDIR /

# Install the dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . /

RUN chmod 777 /run/ -R \
  && chmod 777 /root/ -R

ENV PYTHONPATH '/src'

# Run the command to start uWSGI
CMD ["uwsgi", "--ini", "/docker/flask/uwsgi.ini"]