#!/bin/bash
set -e  # Stop on error

KUBERNETES_DIR="${GIT_REPO_PATH}/kubernetes"

# Preflight: fail fast (and clearly) if the cluster is unreachable, instead of a cryptic
# "connection to the server ... was refused" partway through the applies.
echo "Preflight: verifying the Kubernetes API server is reachable..."
if ! kubectl cluster-info --request-timeout=15s >/dev/null 2>&1; then
  echo "ERROR: Kubernetes API server is unreachable - aborting before any 'kubectl apply'."
  echo "Details:"
  kubectl cluster-info --request-timeout=15s 2>&1 | sed 's/^/  /' || true
  echo "The control plane is likely down, or the kubeconfig points at the wrong host/port."
  echo "On the server, check:  systemctl status kubelet  ;  kubectl cluster-info  ;  that kube-apiserver is listening on :6443."
  exit 1
fi
echo "Kubernetes API server reachable - proceeding with the deploy."

echo "Applying base resources..."
kubectl apply -k ${KUBERNETES_DIR}

echo "Deploying MongoDB first to avoid dependency issues..."
kubectl apply -f "${KUBERNETES_DIR}/deployment/mongo-deployment.yml"
kubectl rollout status deployment/mongo -n aqra --watch=true

echo "Deploying Redis..."
kubectl apply -f "${KUBERNETES_DIR}/deployment/redis-deployment.yml"
kubectl rollout status deployment/redis -n aqra --watch=true

echo "Deploying Flask API..."
kubectl apply -f "${KUBERNETES_DIR}/deployment/flask-deployment.yml"
kubectl rollout status deployment/flask -n aqra --watch=true
