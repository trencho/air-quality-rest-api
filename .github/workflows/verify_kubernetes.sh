#!/bin/bash

source "${GIT_REPO_PATH}"/.github/workflows/hash_directory.sh

KUBERNETES_DIR="${GIT_REPO_PATH}/kubernetes"
KUBERNETES_DIR_SHA_FILE="${GIT_REPO_NAME}_kubernetes_dir_sha"
current_sha=$(hash_directory "${KUBERNETES_DIR}")
if [ -f "${KUBERNETES_DIR_SHA_FILE}" ]; then
  stored_sha=$(cat "${KUBERNETES_DIR_SHA_FILE}")
  if [ "${stored_sha}" = "${current_sha}" ]; then
    echo "SHA values match: The kubernetes directory has not changed."
  else
    echo "SHA values differ: The Kubernetes directory has been modified."
    kubectl apply -f "${KUBERNETES_DIR}"/resources.yml
    kubectl apply -f "${KUBERNETES_DIR}"/mongo-deployment.yml
    kubectl apply -f "${KUBERNETES_DIR}"/single/resources/flask-deployment.yml
  fi
else
  current_sha=$(hash_directory "${KUBERNETES_DIR}")
  echo "File '${KUBERNETES_DIR_SHA_FILE}' created with the current SHA value."
  kubectl apply -f "${KUBERNETES_DIR}"/resources.yml
  kubectl apply -f "${KUBERNETES_DIR}"/mongo-deployment.yml
  kubectl apply -f "${KUBERNETES_DIR}"/single/resources/flask-deployment.yml
fi
echo "${current_sha}" >"${KUBERNETES_DIR_SHA_FILE}"
