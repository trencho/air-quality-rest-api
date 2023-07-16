# Single node kubernetes cluster

###### Initialize single node kubernetes cluster

```
kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=[cluster-endpoint/kubeadm.feit.ukim.edu.mk] \
--cri-socket /run/cri-dockerd.sock
```

###### Taint master node with control plane in order to deploy pods

```
kubectl taint nodes --all node-role.kubernetes.io/control-plane:NoSchedule-
```

###### Apply flannel network for kubernetes pods

```
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

###### Apply metrics server for cluster

```
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
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
kubectl apply -f kubernetes/metallb/metallb-native.yml
kubectl apply -f kubernetes/metallb/ip-address-pool.yml
kubectl apply -f kubernetes/metallb/l2-advertisement.yml
```

###### Apply sealed secrets controller and generate sealed secrets from existing secrets

```
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/controller.yaml

kubeseal < kubernetes/secrets/flask-secret.yml -o yaml > kubernetes/sealed-secrets/flask-sealed-secret.yml
kubeseal < kubernetes/secrets/mongo-secret.yml -o yaml > kubernetes/sealed-secrets/mongo-sealed-secret.yml
```

```
kubectl apply -f kubernetes/sealed-secrets/flask-sealed-secret.yml
kubectl apply -f kubernetes/sealed-secrets/mongo-sealed-secret.yml
```

###### Generate single yml files for applying all necessary kubernetes resources

```
kubectl kustomize kubernetes/single/resources > kubernetes/single/resources.yml
kubectl kustomize kubernetes > kubernetes/resources.yml
```

###### Apply all system resources

```
kubectl apply -f kubernetes/resources.yml
kubectl apply -f kubernetes/mongo-deployment.yml
kubectl apply -f kubernetes/single/resources/flask-deployment.yml
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

###### Follow logs of deployed pod

```
kubectl logs -f [pod-name] -n aqra
```

```
kubectl get pods -n aqra | grep -E 'flask[a-z0-9\-]*' -iwo | tr -d '\n' | xargs kubectl logs -f -n aqra
```

```
kubectl get pods -n aqra | grep -E 'mongo[a-z0-9\-]*' -iwo | tr -d '\n' | xargs kubectl logs -f -n aqra
```

###### Enter bash of deployed pod

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
kubectl delete -f kubernetes/mongo-deployment.yml
kubectl delete -f kubernetes/single/resources/flask-deployment.yml
```

```
kubectl apply -f kubernetes/mongo-deployment.yml
kubectl apply -f kubernetes/single/resources/flask-deployment.yml
```

###### Retrieve sealed secrets from the cluster

```
kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > kubernetes/master.key

kubeseal --recovery-unseal < kubernetes/sealed-secrets/flask-sealed-secret.yml --recovery-private-key kubernetes/master.key -o yaml > \
kubernetes/secrets/flask-secret.yml
kubeseal --recovery-unseal < kubernetes/sealed-secrets/mongo-sealed-secret.yml --recovery-private-key kubernetes/master.key -o yaml > \
kubernetes/secrets/mongo-secret.yml
```

###### Cleanup resources by deleting persistent volumes and used namespaces

```
kubectl delete namespace aqra
kubectl delete namespace cert-manager
kubectl delete namespace ingress-nginx
kubectl delete namespace metallb-system
kubectl delete pv flaskdata-pv mongodata-pv
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