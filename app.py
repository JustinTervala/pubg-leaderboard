from http import HTTPStatus
import json

from fastapi import FastAPI, HTTPException
from redis.cluster import RedisCluster as Redis

from config import load_config, configure_logging


configure_logging()
app = FastAPI(name="PUBG Leaderboards")
config = load_config()
redis = Redis(
    host=config["REDIS_ADDRESS"],
    port=config["REDIS_PORT"],
    password=config["REDIS_PASSWORD"],
)


@app.get("/accounts/{account_id}/leaderboards")
def read_root(account_id: str):
    key = f"account:{account_id}"
    if not redis.exists(key):
        raise HTTPException(
            HTTPStatus.NOT_FOUND.value,
            detail=f"No information found for account {account_id}",
        )
    leaderboards = redis.get(account_id)
    return {"leaderboards": json.loads(leaderboards)}
