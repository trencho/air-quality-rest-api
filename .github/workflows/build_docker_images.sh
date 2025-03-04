#!/bin/bash

source "${GIT_REPO_PATH}"/.github/workflows/hash_directory.sh

SOURCE_DIR="${GIT_REPO_PATH}"
EXCLUDE_KUBERNETES_DIR="kubernetes"
SOURCE_DIR_SHA_FILE="${GIT_REPO_NAME}_source_dir_sha"
current_sha=$(hash_directory "${SOURCE_DIR}" "${EXCLUDE_KUBERNETES_DIR}")
if [ -f "${SOURCE_DIR_SHA_FILE}" ]; then
  stored_sha=$(cat "${SOURCE_DIR_SHA_FILE}")
  if [ "${stored_sha}" = "${current_sha}" ]; then
    echo "SHA values match: The source directory has not changed."
  else
    echo "SHA values differ: The source directory has been modified."
    docker-compose -f "${SOURCE_DIR}"/docker/docker-compose.yml build
  fi
else
  current_sha=$(hash_directory "${SOURCE_DIR}" "${EXCLUDE_KUBERNETES_DIR}")
  echo "File '${SOURCE_DIR_SHA_FILE}' created with the current SHA value."
  docker-compose -f "${SOURCE_DIR}"/docker/docker-compose.yml build
fi
echo "${current_sha}" >"${SOURCE_DIR_SHA_FILE}"
