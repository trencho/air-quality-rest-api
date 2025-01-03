#!/bin/bash

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
if [ -z "$3" ]; then
  echo "Missing tag name, setting to \"prototype\""
  tag_name=prototype
else
  tag_name=$3
fi
if [ -z "$4" ]; then
  echo "Missing tag number, setting to \"latest\""
  tag_number=latest
else
  tag_number=$4
fi

docker build -f "${dockerfile}" -t "${tag_name}":"${tag_number}" .
docker tag "${tag_name}":"${tag_number}" "${username}"/"${tag_name}"
docker push "${username}"/"${tag_name}"
