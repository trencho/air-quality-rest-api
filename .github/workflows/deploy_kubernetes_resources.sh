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

# Apply a Deployment and wait for it, without tripping over stale status.
#
# `kubectl rollout status` reads .status.conditions, which still describe the PREVIOUS
# rollout until the deployment controller has observed this apply. Run back-to-back with
# `kubectl apply`, it therefore reports the OLD result: flask's deploy failed twice with
# "exceeded its progress deadline" emitted ~100ms after the apply, long before the new
# pod had done anything at all. Raising progressDeadlineSeconds does not help, because
# the stale condition is not recomputed until a new rollout is under way.
#
# So: wait for .status.observedGeneration to catch up to .metadata.generation first.
# Only then does rollout status describe THIS rollout.
deploy_and_wait() {
  local name=$1
  local timeout=${2:-10m}

  echo "Deploying ${name}..."
  kubectl apply -f "${KUBERNETES_DIR}/deployment/${name}-deployment.yml"

  local generation observed
  generation=$(kubectl get "deployment/${name}" -n aqra -o jsonpath='{.metadata.generation}')
  for _ in $(seq 1 60); do
    observed=$(kubectl get "deployment/${name}" -n aqra -o jsonpath='{.status.observedGeneration}')
    if [ "${observed:-0}" -ge "${generation:-1}" ]; then
      break
    fi
    sleep 1
  done

  if ! kubectl rollout status "deployment/${name}" -n aqra --watch=true --timeout="${timeout}"; then
    echo "=============================================================="
    echo "ERROR: ${name} did not become ready. Diagnostics follow."
    echo "=============================================================="
    echo "--- pods ---"
    kubectl get pods -n aqra -l "io.kompose.service=${name}" -o wide || true
    echo "--- describe (events are the useful part) ---"
    kubectl describe pod -n aqra -l "io.kompose.service=${name}" | tail -40 || true
    echo "--- current container logs ---"
    kubectl logs -n aqra -l "io.kompose.service=${name}" --tail=60 --all-containers || true
    echo "--- previous container logs (populated if it crash-looped) ---"
    kubectl logs -n aqra -l "io.kompose.service=${name}" --tail=60 --all-containers --previous || true
    return 1
  fi
}

echo "Applying base resources..."
kubectl apply -k ${KUBERNETES_DIR}

# MongoDB first to avoid dependency issues.
deploy_and_wait mongo 10m
deploy_and_wait redis 10m
# Longer: flask's create_app() blocks on a bulk data fetch before the worker binds, and
# its startupProbe allows 15 minutes for that.
deploy_and_wait flask 20m
