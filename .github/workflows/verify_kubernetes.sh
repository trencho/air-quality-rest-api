#!/bin/bash

KUBERNETES_DIR="kubernetes"
KUBERNETES_DIR_SHA_FILE="kubernetes_dir_sha"
current_sha=$(hash_directory "${KUBERNETES_DIR}")
if [ -f "${KUBERNETES_DIR_SHA_FILE}" ]; then
  stored_sha=$(cat "${KUBERNETES_DIR_SHA_FILE}")
  if [ "${stored_sha}" = "${current_sha}" ]; then
    echo "SHA values match: The Kubernetes directory has not changed."
  else
    echo "SHA values differ: The Kubernetes directory has been modified."
    kubectl apply -f kubernetes/resources.yml
  fi
else
  current_sha=$(hash_directory "${KUBERNETES_DIR}")
  echo "File '${KUBERNETES_DIR_SHA_FILE}' created with the current SHA value."
  kubectl apply -f kubernetes/resources.yml
fi
echo "${current_sha}" >"${KUBERNETES_DIR_SHA_FILE}"
