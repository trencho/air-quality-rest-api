echo "Cleaning up unused Docker resources..."
docker system prune -a --volumes --force

#!/bin/bash
set -e  # Stop on error

echo "Restarting deployments..."
kubectl rollout restart deployment flask -n aqra
kubectl rollout restart deployment mongo -n aqra

echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/flask -n aqra --timeout=60s
kubectl rollout status deployment/mongo -n aqra --timeout=60s

echo "Checking pod readiness..."
for deployment in flask mongo; do
  until [[ $(kubectl get pods -n aqra -l app=$deployment -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') == "True" ]]; do
    echo "Waiting for $deployment pod to be ready..."
    sleep 5
  done
done

echo "Cleaning up unused Docker resources..."
docker system prune -a --volumes --force
