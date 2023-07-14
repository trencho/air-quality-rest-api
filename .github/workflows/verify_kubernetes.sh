#!/bin/bash

cd "${GIT_REPO_PATH}" || exit
KUBERNETES_DIR="kubernetes"
KUBERNETES_DIR_SHA_FILE="kubernetes_dir_sha"

# Check if the file "kubernetes_dir_sha" exists
if [ -f "${KUBERNETES_DIR_SHA_FILE}" ]; then
  # Read the stored SHA value from the file
  stored_sha=$(cat "${KUBERNETES_DIR_SHA_FILE}")

  # Calculate the SHA value of the Kubernetes directory
  current_sha=$(find "${KUBERNETES_DIR}" -type d -exec sha1sum {} + | awk '{print $1}' | sort | sha1sum | awk '{print $1}')

  # Compare the stored and current SHA values
  if [ "${stored_sha}" = "${current_sha}" ]; then
    echo "SHA values match: The Kubernetes directory has not changed."
  else
    echo "SHA values differ: The Kubernetes directory has been modified."
    # Apply the changed kubernetes resources
    kubectl apply -f kubernetes/resources.yml
  fi
else
  # Calculate the SHA value of the Kubernetes directory
  current_sha=$(find "${KUBERNETES_DIR}" -type d -exec sha1sum {} + | awk '{print $1}' | sort | sha1sum | awk '{print $1}')

  # Create the file and store the SHA value
  echo "${current_sha}" >"${KUBERNETES_DIR_SHA_FILE}"
  echo "File '${KUBERNETES_DIR_SHA_FILE}' created with the current SHA value."
  # Apply the changed kubernetes resources
  kubectl apply -f kubernetes/resources.yml
fi
