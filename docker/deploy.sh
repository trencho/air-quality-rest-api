#!/bin/bash

# Check for required arguments
if [ -z "$1" ]; then
  echo "You must specify a Dockerfile!"
  exit 1
else
  dockerfile=$1
fi

if [ -z "$2" ]; then
  echo "You must specify a Docker Hub username!"
  exit 1
else
  username=$2
fi

# Set optional arguments with default values
tag_name=${3:-"prototype"}
tag_number=${4:-"latest"}

# Build, tag, and push the Docker image
docker build -f "${dockerfile}" -t "${tag_name}:${tag_number}" .
docker tag "${tag_name}:${tag_number}" "${username}/${tag_name}"
docker push "${username}/${tag_name}"
