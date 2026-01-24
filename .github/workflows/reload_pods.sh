#!/bin/bash
set -e  # Stop on error

kubectl rollout restart deployment mongo -n aqra
kubectl rollout restart deployment flask -n aqra

echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/mongo -n aqra --watch=true
kubectl rollout status deployment/flask -n aqra --watch=true

echo "Cleaning up unused Docker resources..."
docker system prune -a --volumes --force
