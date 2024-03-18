# PUBG Leaderboard Scraper
This system polls the [PUBG API](https://developer.pubg.com) daily and gathers the leaderboard for all the current seasons and stores the results in a Redis cluster keyed by the player account ID. In the Redis databse, each key of the form `account:<id>` contains a JSON string of the format

```json
[
    {
        "platform_region": "pc-na",
        "season": "division.bro.official.pc-2018-28",
        "game_mode": "solo",
        "rank" 1,
        "games": 1587,
        "wins": 1337,
    }
]
```

A player can be on the leaderboard for multiple platform regions, game modes, or seasons. For more information on `platform_region`, `season`, and `game_mode`, see the [relevant section of the docs](https://documentation.pubg.com/en/making-requests.html). 

An API server is also provided which can fetch this information at the URL `/accounts/{account-id}/leaderboards`.

## Infrastructure
The system is deployed locally on a minikube cluster with two namespaces: `pubg`, and `monitoring`.

### pubg Namespace Contents
- A Redis Cluster deployed via the [Bitnami Helm Chart](https://github.com/bitnami/charts/tree/main/bitnami/redis-cluster) acessibe at `pubg-redis-cluster:6379`.
- A ConfigMap containing the Redis cluster host and port
- ServiceAccount named `pubg`
- A CronJob named `pubg-scraper`
  - Runs every day at midnight UTC
- A Job named `pubg-oneoff-scrape`
  - To run the API polling job on demand
- A webapp which provides an API to the Redis cluster and is composed on
    - Deployment named `pubg-app`
    - NodePort Service named `pubg`
    - HPA named `pubg-app`
    - NGINX-Ingress named `pubg` which exposes the app
        - _I couldn't get this working with minikube on either my very busted 2019 Intel MacOs or brand new 2023 M3 MacOs, but for very different reasons. Theoretically, it might work for others?_

### monitoring Namespace Contents
- A Prometheus stack from the [Prometheus Community Helm Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus)
- A Grafana stack from the [Offical Grafana Helm Chart](https://github.com/grafana/helm-charts/blob/main/charts/grafana)
- An NGINX Ingress which should theoretically expose both the prometheus and grafana services
- 2GB PersistentVolumes mounted to `/data/prometheus` and `/data/grafana` locally and corresponding PVCs

## Installation
0. Get a Developer API Key from PUBG [here](https://documentation.pubg.com/en/api-keys.html)
1. Install Prerequisites (on MacOs)
```
brew install minikube helm docker
```

2. Start Docker

3. (Optional) Configure Helm values in `infra/values` directory

4. Run the startup script
```
export PUBG_API_KEY=<your-api-key-here>
./run.sh
```
This will
- Start minikube
- Build the Docker image for this project
- Add the Redis Cluster, Prometheus, and Grafana Helm repos
- Add the namespaces, service account, and volumes to the cluster
- Install the Redis Cluster, Prometheus, and Grafana stacks
- Create config maps and secrets
- Start an initial Job to pull the PUBG data into Redis
- Add the cronjob, API, and ingress

## Operating

### Querying the API
1. Run `minikube service pubg --url -n pubg`. This should display a URL. Keey this tab open adn running.
2. In another tab, run `curl <url>/accounts/<account-id>/leaderboards`
3. Swagger Docs can be viewed in your browser at `<url>/docs`

### Inspecting the Redis cluster
1. Run `./redis-cli.sh` and when prompted, press ENTER
2. Enter `redis-cli -h pubg-redis-cluster -a $REDIS_PASSWORD`

### Connecting to AWS IRSA
This hasn't been tested, but according to the [AWS docs](https://aws.amazon.com/blogs/opensource/introducing-fine-grained-iam-roles-service-accounts/), you should be able to run
```
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
kubectl annotate sa pubg eks.amazonaws.com/role-arn=$MY_ROLE_ARN -n pubg
```

### Getting the Grafana login
The username is `admin`. To get the password, run
`kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo`


### Updating the secrets
After updating the .env.secrets, run
```
kubectl create secret generic pubg-scraper-secret \
    --save-config \
    --dry-run=client \
    --from-file=.env.secret \
    -o yaml | \
    kubectl apply -f -
```

## Development
Both the job and the app are written in Python 3.9 and use [Poetry](https://python-poetry.org) for environment management.

### Configuration
Configuration is done through [dotenv](https://github.com/theskumar/python-dotenv) files. In order of preferce, configuration is loaded from `.env`, `.env.secret`, and environment variables. The avilable configuration is REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, and PUBG_API_KEY. You can create a local .env file manually or using the dotenv cli e.g. `poetry run dotenv set REDIS_HOST localhost`. For either the job or the app to run outside of the cluster, you'll need to start a redis server in a terminal and configure the REDIS_HOST and REDIS_PORT appropriately.
### Running the job locally
To run the API scrape job locally, you can run
`poetry run python pubg/job.py`. Because the rate limit for the PUBG API is 0 requsts per minute, this job take a long time complete. For rapid development, you can enable reading and writing to a local cache using the options `--use-cache` and `--cache-dir`. For quickly testing the entire pipeline, there is also a `--quick` option which will limit the number of leaderboards read to 5.

### Linting
To lint the Python code, run `poetry run black pubg`