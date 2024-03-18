# Install dependencies


```ShellSession
$: brew install minikube docker helm
```

Verify install (more here)
```
minikube version
```
start docker

Start minikube
```
minikube start
```
configure minikube to work with local docker
```
eval $(minikube docker-env)
```

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
  
kubectl apply -f infra/namespace.yaml
kubectl apply -f infra/monitoring-volumes.yaml
helm install prometheus prometheus-community/prometheus --namespace monitoring -f infra/values/prom.yaml
helm install grafana grafana/grafana --namespace monitoring -f infra/values/grafana.yaml
helm install pubg-redis oci://registry-1.docker.io/bitnamicharts/redis-cluster --namespace pubg -f infra/values/redis.yaml
kubectl apply -f infra/redis-config.yaml


Add secrets

echo MY_API_KEY >> .env.secret
export REDIS_PASSWORD=$(kubectl get secret --namespace "pubg" pubg-redis-cluster -o jsonpath="{.data.redis-password}" | base64 -d)
echo "REDIS_PASSWORD=\"$REDIS_PASSWORD\"" >> .env.secret
kubectl create secret generic pubg-scraper-secret --from-file .env.secret --namespace pubg


Enable NGINX ingress
minikube addons enable ingress
kubectl apply -f ingress.yaml

to send a curl
minikube service pubg --url -n pubg
In another tab
curl <url>/accounts/<account_id>/leaderboards

# This was untested
according to https://aws.amazon.com/blogs/opensource/introducing-fine-grained-iam-roles-service-accounts/

export CLUSTER_NAME=<cluster-name-here>
eksctl utils associate-iam-oidc-provider \
               --name $CLUSTER_NAME \
               --approve
ISSUER_URL=$(aws eks describe-cluster \
                       --name irptest \
                       --query cluster.identity.oidc.issuer \
                       --output text)
aws iam create-open-id-connect-provider \
          --url $ISSUER_URL \
          --thumbprint-list $ROOT_CA_FINGERPRINT \
          --client-id-list sts.amazonaws.com
export POLICY_ARN=<some ARN here>
// ex. arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
eksctl create iamserviceaccount \
                --name pubg-sa \
                --namespace pubg \
                --cluster $CLUSTER_NAME \
                --attach-policy-arn $POLICY_ARN \
                --approve

Alternatively, you could run
kubectl annotate sa pubg-sa eks.amazonaws.com/role-arn=$MY_ROLE_ARN

Then creating the deplopyments should be connected to the IAM role


to update the redis secret (after redeploying redis for example)
kubectl create secret generic pubg-scraper-secret \
    --save-config \
    --dry-run=client \
    --from-file=.env.secret \
    -o yaml | \
    kubectl apply -f -


The Prometheus PushGateway can be accessed via port 9091 on the following DNS name from within your cluster:
prometheus-prometheus-pushgateway.monitoring.svc.cluster.local


Get the PushGateway URL by running these commands in the same shell:
  export POD_NAME=$(kubectl get pods --namespace monitoring -l "app=prometheus-pushgateway,component=pushgateway" -o jsonpath="{.items[0].metadata.name}")
  kubectl --namespace monitoring port-forward $POD_NAME 9091


  1. Get your 'admin' user password by running:

   kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

2. The Grafana server can be accessed via port 80 on the following DNS name from within your cluster:

   grafana.monitoring.svc.cluster.local

   Get the Grafana URL to visit by running these commands in the same shell:
     export POD_NAME=$(kubectl get pods --namespace monitoring -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=grafana" -o jsonpath="{.items[0].metadata.name}")
     kubectl --namespace monitoring port-forward $POD_NAME 3000

3. Login with the password from step 1 and the username: admin

https://semaphoreci.com/blog/prometheus-grafana-kubernetes-helm



To get grafana password
kubectl get secret --namespace monitoring  grafana -o jsonpath="{.data.admin-password}" | base64 --decode