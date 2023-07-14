#!/bin/bash

mkdir -p "${GIT_REPO_PATH}"
chown "${SSH_USERNAME}":"${SSH_USERNAME}" "${GIT_REPO_PATH}"
if [ ! -d "${GIT_REPO_PATH}"/.git ]; then
  git clone https://"${ACCESS_TOKEN}"@github.com/"${GIT_REPO_USERNAME}"/"${GIT_REPO_NAME}".git "${GIT_REPO_PATH}"
fi
cd "${GIT_REPO_PATH}" || exit
git fetch origin
git reset --hard origin/master
