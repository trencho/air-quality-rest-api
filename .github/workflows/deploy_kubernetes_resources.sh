#!/bin/bash

KUBERNETES_DIR="${GIT_REPO_PATH}/kubernetes"
kubectl apply -f "${KUBERNETES_DIR}"/resources.yml
kubectl apply -f "${KUBERNETES_DIR}"/mongo-deployment.yml
kubectl apply -f "${KUBERNETES_DIR}"/single/resources/flask-deployment.yml
