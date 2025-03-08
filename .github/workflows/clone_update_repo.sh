#!/bin/bash
set -e  # Exit on error

mkdir -p "${GIT_REPO_PATH}"

if [ ! -d "${GIT_REPO_PATH}/.git" ]; then
  echo "Repository not found. Cloning..."
  git clone https://"${ACCESS_TOKEN}"@github.com/"${GIT_REPO_USERNAME}"/"${GIT_REPO_NAME}".git "${GIT_REPO_PATH}"
else
  echo "Repository found. Fetching latest changes..."
  cd "${GIT_REPO_PATH}" || exit
  git fetch origin
  git reset --hard origin/master
fi

echo "Setting correct ownership..."
chown -R "${SSH_USERNAME}:${SSH_USERNAME}" "${GIT_REPO_PATH}"
