FROM ubuntu:19.10

MAINTAINER Aleksandar Trenchevski <atrenchevski@gmail.com>

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev && \
    apt-get install -y nginx uwsgi uwsgi-plugin-python3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./requirements.txt /requirements.txt
COPY ./nginx.conf /etc/nginx/nginx.conf

WORKDIR /

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /

RUN adduser --disabled-password --gecos '' nginx \
  && chown -R nginx:nginx /src/api \
  && chmod 777 /run/ -R \
  && chmod 777 /root/ -R

ENV PYTHONPATH "/src"

ENTRYPOINT [ "/bin/bash", "/launch.sh"]