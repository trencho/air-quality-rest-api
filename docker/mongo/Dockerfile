FROM mongo

LABEL maintainer="Aleksandar Trenchevski <atrenchevski@gmail.com>"

ARG USER_ID=1000
ARG USER_GID=1000
ARG USER_NAME=mongo
RUN addgroup --gid $USER_GID $USER_NAME && \
    adduser --disabled-password --gecos "" --uid $USER_ID --gid $USER_GID $USER_NAME && \
    chown -R $USER_ID:$USER_GID /data/db

# Set the user for subsequent instructions
USER $USER_NAME

EXPOSE 27017

CMD ["mongod", "--auth"]