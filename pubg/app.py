from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from redis.cluster import RedisCluster as Redis

from .config import configure_logging, load_config
from .models import PlayerRank


configure_logging()
app = FastAPI(name="PUBG Leaderboards")
config = load_config()

# This should really have a retry loop to ensure k8s resources creation aren't dependent on order
redis = Redis(
    host=config["REDIS_HOST"],
    port=config["REDIS_PORT"],
    password=config["REDIS_PASSWORD"],
)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/healthz",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")


@app.get("/accounts/{account_id}/leaderboards")
def read_root(account_id: str):
    key = f"account:{account_id}"
    if not redis.exists(key):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"No information found for account {account_id}",
        )
    leaderboards = redis.get(account_id)
    return {"leaderboards": PlayerRank(**leaderboards)}
