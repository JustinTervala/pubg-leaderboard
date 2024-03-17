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

Create namespace    
kubectl apply -f namespace.yaml




__ can add -f values.yaml for config__

helm install pubg-redis oci://registry-1.docker.io/bitnamicharts/redis-cluster --namespace pubg -f infra/redis-values.yaml

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
kubectl create secret generic pubg-scraper-secret --from-file .env.secret --namespace pubg


Local testing
kubectl port-forward pubg-redis-cluster 6379:6379
poetry run app.py

Enable NGINX ingress
minikube addons enable ingress


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


