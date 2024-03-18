#!/usr/bin/env bash


minikube start
eval $(minikube docker-env)
minikube addons enable ingress

docker build . -t pubg-scraper

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
kubectl apply -f infra/namespace.yaml
kubectl apply -f infra/sa.yaml
kubectl apply -f infra/monitoring.yaml --namespace monitoring
helm install prometheus prometheus-community/prometheus --namespace monitoring -f infra/values/prom.yaml
helm install grafana grafana/grafana --namespace monitoring -f infra/values/grafana.yaml
helm install pubg oci://registry-1.docker.io/bitnamicharts/redis-cluster --namespace pubg -f infra/values/redis.yaml
kubectl apply -f infra/redis-config.yaml --namespace pubg

export REDIS_PASSWORD=$(kubectl get secret --namespace "pubg" pubg-redis-cluster -o jsonpath="{.data.redis-password}" | base64 -d)
echo "REDIS_PASSWORD=\"$REDIS_PASSWORD\"" >> .env.secret
kubectl create secret generic pubg-scraper-secret --from-file .env.secret --namespace pubg
kubectl apply -f infra/initial-job.yaml -n pubg
kubectl apply -f infra/cronjob.yaml -n pubg
kubectl apply -f infra/app.yaml -n pubg
kubectl apply -f infra/ingress.yaml -n pubg

