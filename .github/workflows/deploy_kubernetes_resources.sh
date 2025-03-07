#!/bin/bash
set -e  # Stop on error

KUBERNETES_DIR="${GIT_REPO_PATH}/kubernetes"

echo "Applying base resources..."
kubectl apply -f "${KUBERNETES_DIR}/resources.yml"

echo "Deploying MongoDB first to avoid dependency issues..."
kubectl apply -f "${KUBERNETES_DIR}/deployment/mongo-deployment.yml"
kubectl rollout status deployment/mongo -n aqra --timeout=60s

echo "Deploying Flask API..."
kubectl apply -f "${KUBERNETES_DIR}/deployment/flask-deployment.yml"
kubectl rollout status deployment/flask -n aqra --timeout=60s
