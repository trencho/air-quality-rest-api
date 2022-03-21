# Single node kubernetes cluster

###### Initialize single node kubernetes cluster

kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=[cluster-endpoint]

###### Taint master node with control plane in order to deploy pods

kubectl taint nodes --all node-role.kubernetes.io/master-

###### Generate single yml files for applying all necessary kubernetes resources

kubectl kustomize kubernetes > kubernetes/resources.yml  
kubectl kustomize kubernetes/single/resources > kubernetes/single/resources.yml

###### Apply flannel network for kubernetes pods

kubectl apply -f https://github.com/coreos/flannel/raw/master/Documentation/kube-flannel.yml

###### Apply cert-manager resources

kubectl apply -f https://github.com/jetstack/cert-manager/releases/latest/download/cert-manager.yaml

###### Apply ingress-nginx resources with values from a custom yml file

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace --values \
kubernetes/ingress-nginx.yml

###### Apply MetalLB resources for deploying a load balancer

kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.12.1/manifests/namespace.yaml  
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.12.1/manifests/metallb.yaml  
kubectl apply -f kubernetes/metallb-configmap.yml

###### Apply sealed secrets controller and generate sealed secrets from existing secrets

kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/controller.yaml  
kubeseal < kubernetes/secrets/flask-secret.yml -o yaml > kubernetes/sealed-secrets/flask-sealed-secret.yml  
kubeseal < kubernetes/secrets/mongo-secret.yml -o yaml > kubernetes/sealed-secrets/mongo-sealed-secret.yml

kubectl apply -f kubernetes/sealed-secrets/flask-sealed-secret.yml  
kubectl apply -f kubernetes/sealed-secrets/mongo-sealed-secret.yml

###### Apply all system resources

kubectl apply -f kubernetes/resources.yml  
kubectl apply -f kubernetes/single/resources.yml

###### Get deployed pods in namespace aqra

kubectl get pods -n aqra

###### Follow logs of deployed pod

kubectl logs -f [pod-name] -n aqra

###### Enter bash of deployed pod

kubectl exec -n aqra --stdin --tty [pod-name] -- /bin/bash

###### Delete and reapply deployments if changes are made to the Docker images

kubectl delete -f kubernetes/mongo-deployment.yml  
kubectl delete -f kubernetes/single/resources/flask-deployment.yml  
kubectl apply -f kubernetes/mongo-deployment.yml  
kubectl apply -f kubernetes/single/resources/flask-deployment.yml

###### Retrieve sealed secrets from the cluster

kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > kubernetes/master.key  
kubeseal --recovery-unseal < kubernetes/flask-sealed-secret.yml --recovery-private-key kubernetes/master.key -o yaml > \
kubernetes/flask-secret.yml  
kubeseal --recovery-unseal < kubernetes/mongo-sealed-secret.yml --recovery-private-key kubernetes/master.key -o yaml > \
kubernetes/mongo-secret.yml

###### Cleanup resources by deleting persistent volumes and used namespaces

kubectl delete namespace aqra  
kubectl delete namespace cert-manager  
kubectl delete namespace ingress-nginx  
kubectl delete namespace metallb-system kubectl delete pv flaskdata-pv mongodata-pv

###### Reset kubernetes cluster

kubeadm reset

###### Upgrade the kubernetes cluster

kubeadm upgrade plan  
kubeadm upgrade apply latest