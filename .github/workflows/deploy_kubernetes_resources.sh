#!/bin/bash

KUBERNETES_DIR="${GIT_REPO_PATH}/kubernetes"
kubectl apply -f "${KUBERNETES_DIR}"/resources.yml
kubectl apply -f "${KUBERNETES_DIR}"/deployment/flask-deployment.yml
kubectl apply -f "${KUBERNETES_DIR}"/deployment/mongo-deployment.yml
