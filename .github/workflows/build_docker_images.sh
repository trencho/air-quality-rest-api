#!/bin/bash
set -e  # Stop on error

source "${GIT_REPO_PATH}"/.github/workflows/hash_directory.sh

SOURCE_DIR="${GIT_REPO_PATH}"
EXCLUDE_KUBERNETES_DIR="kubernetes"
SOURCE_DIR_SHA_FILE="${GIT_REPO_PATH}/../${GIT_REPO_NAME}_source_dir_sha"

current_sha=$(hash_directory "${SOURCE_DIR}" ".github" "${EXCLUDE_KUBERNETES_DIR}")

if [[ -f "${SOURCE_DIR_SHA_FILE}" ]] && [[ "$(cat "${SOURCE_DIR_SHA_FILE}")" == "${current_sha}" ]]; then
  echo "No changes detected in source directory. Skipping build."
  exit 0
fi

echo "Changes detected. Building Docker images..."
docker-compose -f "${SOURCE_DIR}/docker/docker-compose.yml" build

echo "${current_sha}" > "${SOURCE_DIR_SHA_FILE}"
