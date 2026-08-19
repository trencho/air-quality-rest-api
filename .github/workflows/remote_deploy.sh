#!/usr/bin/env bash
# The remote half of the deploy, executed on the server over SSH.
#
# It lives in a file rather than inline in build-deploy.yml so the retry step can point
# at it instead of carrying a second copy. Two copies of a forty-line deploy script is
# exactly the kind of duplication that drifts.
#
# ACCESS_TOKEN, GIT_REPO_NAME, GIT_REPO_PATH, GIT_REPO_USERNAME and SSH_USERNAME reach
# this shell through the action's `envs:` input, so they are no longer interpolated into
# the script text either.
#
# Idempotent by construction, which is what makes retrying it safe: the checkout is a
# `git reset --hard`, and the deploy is `kubectl apply` plus read-only rollout waits.
set -e # Stop execution on any error

echo "Cloning/Updating repository..."
mkdir -p "${GIT_REPO_PATH}"

if [ ! -d "${GIT_REPO_PATH}/.git" ]; then
  echo "Repository not found. Cloning..."
  git clone https://"${ACCESS_TOKEN}"@github.com/"${GIT_REPO_USERNAME}"/"${GIT_REPO_NAME}".git "${GIT_REPO_PATH}"
  cd "${GIT_REPO_PATH}" || exit
else
  echo "Repository found. Fetching latest changes..."
  cd "${GIT_REPO_PATH}" || exit
  git fetch origin
  git reset --hard origin/master
fi

echo "Setting correct ownership..."
chown -R "${SSH_USERNAME}:${SSH_USERNAME}" "${GIT_REPO_PATH}"

echo "Making scripts executable..."
find .github/workflows -type f -name "*.sh" -exec chmod +x {} +

echo "Executing deployment scripts..."
.github/workflows/deploy_kubernetes_resources.sh

echo "Restarting Kubernetes Deployments..."
.github/workflows/reload_pods.sh

echo "Deployment successful!"
