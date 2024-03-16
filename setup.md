# Install dependencies

```ShellSession
$: brew isntall minikube docker helm
```
If you are on an apple m3, then 
```brew install qemu```

Start docker

Verify install
```
minikube version
```

configure docker to use local docker
```
eval $(minikube docker-env)
```
Start minikube
```
minikube start
```
If on an M-series chip, follow isntructions at https://devopscube.com/minikube-mac/
minikube start --driver qemu --network socker_wmnet

Create namespace    
kubectl apply -f namespace.yaml


adjust context
kubectl config set-context $(kubectl config current-context) --namespace=pubg


__ can add -f values.yaml for config__

helm install pubg oci://registry-1.docker.io/bitnamicharts/redis-cluster

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
help repo add bitnami 
helm repo update

https://semaphoreci.com/blog/prometheus-grafana-kubernetes-helm

to instrument with emtrics use a push gateway

https://stackoverflow.com/questions/5zz4920309/monitoring-short-lived-python-batch-job-processes-using-prometheus

Add secrets

echo MY_API_KEY >> .env.secret
export REDIS_PASSWORD=$(kubectl get secret --namespace "pubg" pubg-redis-cluster -o jsonpath="{.data.redis-password}" | base64 -d)
echo "REDIS_PASSWORD=\"$REDIS_PASSWORD\"" >> .env.secret


Local testing
kubectl port-forward pubg-redis-cluster 6379:6379
poetry run app.py

Enable NGINX ingress
minikube addons enable ingress


to send a curl
minikube service pubg --url -n pubg
In another tab
curl <url>/accounts/<account_id>/leaderboards