# Single node kubernetes cluster

###### Initialize single node kubernetes cluster

```
kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=kubeadm.feit.ukim.edu.mk --cri-socket unix:///run/docker.sock
```

```
kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=kubeadm.feit.ukim.edu.mk --cri-socket unix:///run/containerd/containerd.sock
```

```
kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=kubeadm.feit.ukim.edu.mk --cri-socket unix:///run/cri-dockerd.sock
```

###### Taint the master node with control plane to deploy pods

```
kubectl taint nodes --all node-role.kubernetes.io/control-plane:NoSchedule-
```

###### Apply flannel network for kubernetes pods

```
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

###### Apply metrics server for cluster

```
kubectl apply -f kubernetes/metrics-server/components.yml
```

###### Apply cert-manager resources

```
kubectl apply -f https://github.com/jetstack/cert-manager/releases/latest/download/cert-manager.yaml
```

###### Apply ingress-nginx resources with values from a custom yml file

```
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace --values \
kubernetes/custom-ingress-values.yml
```

###### Apply MetalLB resources for deploying a load balancer

```
kubectl apply -f kubernetes/metallb/ip-address-pool.yml
kubectl apply -f kubernetes/metallb/l2-advertisement.yml
kubectl apply -f kubernetes/metallb/metallb-native.yml
```

###### Apply sealed secrets controller and generate sealed secrets from existing secrets

```
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.28.0/controller.yaml

kubeseal < kubernetes/secret/flask-secret.yml -o yaml > kubernetes/sealed-secret/flask-sealed-secret.yml
kubeseal < kubernetes/secret/mongo-secret.yml -o yaml > kubernetes/sealed-secret/mongo-sealed-secret.yml
```

```
kubectl apply -f kubernetes/sealed-secret/flask-sealed-secret.yml
kubectl apply -f kubernetes/sealed-secret/mongo-sealed-secret.yml
```

###### Generate single yml files for applying all necessary kubernetes resources

```
kubectl kustomize kubernetes > kubernetes/resources.yml
```

###### Apply all system resources

```
kubectl apply -f kubernetes/resources.yml
kubectl apply -f kubernetes/deployment/flask-deployment.yml
kubectl apply -f kubernetes/deployment/mongo-deployment.yml
```

###### Get deployed pods in namespace aqra

```
kubectl get pods -n aqra
```

###### Describe deployed pods

```
kubectl describe pod [pod-name] -n aqra
```

```
kubectl get pods -n aqra | grep -E 'flask[a-z0-9\-]*' -iwo | tr -d '\n' | xargs kubectl describe pod -n aqra
```

```
kubectl get pods -n aqra | grep -E 'mongo[a-z0-9\-]*' -iwo | tr -d '\n' | xargs kubectl describe pod -n aqra
```

###### Follow logs of the deployed pod

```
kubectl logs -f [pod-name] -n aqra
```

```
kubectl get pods -n aqra | grep -E 'flask[a-z0-9\-]*' -iwo | tr -d '\n' | xargs kubectl logs -f -n aqra
```

```
kubectl get pods -n aqra | grep -E 'mongo[a-z0-9\-]*' -iwo | tr -d '\n' | xargs kubectl logs -f -n aqra
```

###### Enter bash of the deployed pod

```
kubectl exec -n aqra --stdin --tty [pod-name] -- /bin/bash
```

```
kubectl exec -n aqra --stdin --tty $(kubectl get pods -n aqra | grep -E 'flask[a-z0-9\-]*' -iwo | tr -d '\n') -- /bin/bash
```

```
kubectl exec -n aqra --stdin --tty $(kubectl get pods -n aqra | grep -E 'mongo[a-z0-9\-]*' -iwo | tr -d '\n') -- /bin/bash
```

###### Delete and reapply deployments if changes are made to the Docker images

```
kubectl delete -f kubernetes/deployment/flask-deployment.yml
kubectl delete -f kubernetes/deployment/mongo-deployment.yml
```

```
kubectl apply -f kubernetes/deployment/flask-deployment.yml
kubectl apply -f kubernetes/deployment/mongo-deployment.yml
```

###### Retrieve sealed secrets from the cluster

```
kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > kubernetes/master.key

kubeseal --recovery-unseal < kubernetes/sealed-secret/flask-sealed-secret.yml --recovery-private-key kubernetes/master.key -o yaml > \
kubernetes/secret/flask-secret.yml
kubeseal --recovery-unseal < kubernetes/sealed-secret/mongo-sealed-secret.yml --recovery-private-key kubernetes/master.key -o yaml > \
kubernetes/secret/mongo-secret.yml
```

###### Cleanup resources by deleting persistent volumes and used namespaces

```
kubectl delete namespace aqra
kubectl delete namespace cert-manager
kubectl delete namespace ingress-nginx
kubectl delete namespace metallb-system
kubectl delete pv flask-data-pv mongo-data-pv
```

###### Reset kubernetes cluster

```
kubeadm reset
```

###### Upgrade the kubernetes cluster

```
kubeadm upgrade plan
kubeadm upgrade apply latest
```