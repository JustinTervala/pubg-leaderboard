# Install dependencies

```ShellSession
$: brew isntall minikube docker helm
```
Start docker

Verify install
```
minikube version
```

configure docker to use local docker
```
eval $(minikube docker-env)
minikube start
```

Create namespace
kubectl apply -f namespace.yaml


adjust context
kubectl config set-context $(kubectl config current-context) --namespace=pubg


__ can add -f values.yaml for config__

helm install pubg oci://registry-1.docker.io/bitnamicharts/redis-cluster

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

https://semaphoreci.com/blog/prometheus-grafana-kubernetes-helm

to instrument with emtrics use a push gateway

https://stackoverflow.com/questions/5zz4920309/monitoring-short-lived-python-batch-job-processes-using-prometheus

