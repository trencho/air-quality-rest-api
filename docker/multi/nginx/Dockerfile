FROM nginx:latest

LABEL maintainer="Aleksandar Trenchevski <atrenchevski@gmail.com>"

RUN rm /etc/nginx/conf.d/default.conf
COPY ./docker/nginx.conf /etc/nginx/conf.d/

EXPOSE 80