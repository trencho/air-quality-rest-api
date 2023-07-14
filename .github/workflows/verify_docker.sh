#!/bin/bash

SOURCE_DIR="${GIT_REPO_PATH}"
EXCLUDE_KUBERNETES_DIR="kubernetes"
SOURCE_DIR_SHA_FILE="source_dir_sha"

# Check if the file "source_dir_sha" exists
if [ -f "${SOURCE_DIR_SHA_FILE}" ]; then
  # Read the stored SHA value from the file
  stored_sha=$(cat "${SOURCE_DIR_SHA_FILE}")

  # Calculate the SHA value of the source directory
  current_sha=$(find "${SOURCE_DIR}" -type d -not -path "${EXCLUDE_KUBERNETES_DIR}/*" -not -name "*dir_sha" -exec sha1sum {} + | awk '{print $1}' | sort | sha1sum | awk '{print $1}')

  # Compare the stored and current SHA values
  if [ "$stored_sha" = "$current_sha" ]; then
    echo "SHA values match: The source directory has not changed."
  else
    echo "SHA values differ: The source directory has been modified."
    docker-compose -f docker/single/docker-compose.yml build
  fi
else
  # Calculate the SHA value of the source directory
  current_sha=$(find "${SOURCE_DIR}" -type d -not -path "${EXCLUDE_KUBERNETES_DIR}/*" -not -name "*dir_sha" -exec sha1sum {} + | awk '{print $1}' | sort | sha1sum | awk '{print $1}')

  # Create the file and store the SHA value
  echo "${current_sha}" >"${SOURCE_DIR_SHA_FILE}"
  echo "File '${SOURCE_DIR_SHA_FILE}' created with the current SHA value."
  docker-compose -f docker/single/docker-compose.yml build
fi
