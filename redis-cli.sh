#!/usr/bin/env bash

export REDIS_PASSWORD=$(kubectl get secret --namespace "pubg" pubg-redis-cluster -o jsonpath="{.data.redis-password}" | base64 -d)
kubectl run redis-cli -n pubg --image redis:latest --attach --env REDIS_PASSWORD=$REDIS_PASSWORD --rm -it -- sh
# redis-cli -h redis-master -a $REDIS_PASSWORD