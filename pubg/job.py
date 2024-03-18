import time
import sys
import json
from collections import defaultdict
import argparse
from pathlib import Path
from typing import Any, Iterable, Optional, Union
import os
import logging

from pydantic import BaseModel, Field
from requests_ratelimiter import LimiterSession
from dotenv import dotenv_values
from redis.cluster import RedisCluster as Redis
import click

from config import load_config, configure_logging
from models import (
    Season,
    SeasonLeaderboard,
    GameMode,
    LeaderboardKey,
    LeaderboardPlayer,
    PlayerRank,
)


logger = logging.getLogger(__name__)

configure_logging()
config = load_config()


headers = {
    "Accept": "application/vnd.api+json",
    "Accept-Encoding": "gzip",
    "User-Agent": "pubg-leader-updater",  # TODO: Add version getter here
    "Authorization": f"Bearer {config['PUBG_API_KEY']}",
}

session = LimiterSession(per_minute=9)

platform_regions = {
    "pc": ["as", "eu", "jp", "kakao", "krjp", "na", "oc", "ru", "sa", "sea"],
    "psn": ["as", "eu", "na", "oc"],
    "xbox": ["as", "eu", "na", "oc", "sa"],
}
platform_to_platform_region = {
    "kakao": ["pc"],
    "stadia": ["psn", "xbox"],
    "steam": ["pc"],
    "psn": ["psn"],
    "xbox": ["xbox"],
    "console": ["psn", "xbox"],
}

seasons_url = (
    "https://api.pubg.com/shards/{shard}/seasons"  # This should be cached by the month
)
leaderboard_url = "https://api.pubg.com/shards/{shard}/leaderboards/{season_id}/{game_mode}"  # TODO format this properly


def iter_platform_regions() -> Iterable[str]:
    for base, regions in platform_regions.items():
        for region in regions:
            yield f"{base}-{region}"


def get_current_season(shard: str) -> Optional[str]:
    seasons_resp = session.get(seasons_url.format(shard=shard), headers=headers)
    if not seasons_resp.ok:
        logger.error(f"Getting season for {shard} failed: {seasons_resp}")
        return None
    seasons = [Season(**s) for s in seasons_resp.json()["data"]]
    for season in seasons:
        attr = season.attributes
        if season.attributes.is_current_season:
            logger.info(f"Current season for {shard}: {season.id}")
            return season.id
    logger.warning(f"{shard} has no current season")
    return None


def iter_leaderboards() -> Iterable[LeaderboardKey]:
    for platform_region in iter_platform_regions():
        if current_season := get_current_season(platform_region):
            for game_mode in GameMode.current_modes():
                yield LeaderboardKey(
                    platform_region=platform_region,
                    season=current_season,
                    game_mode=game_mode,
                )


def get_leaderboards(
    quick: bool = False,
) -> dict[LeaderboardKey, list[LeaderboardPlayer]]:
    leaderboards = {}
    i = 0
    logger.info("Scraping leaderboards...")
    out = []
    for key in iter_leaderboards():
        i += 1
        if quick and i > 5:
            logger.info("Ending early becuase --quick is enabled")
            break
        leaderboard_resp = session.get(
            leaderboard_url.format(
                shard=key.platform_region,
                season_id=key.season,
                game_mode=key.game_mode.value,
            ),
            headers=headers,
        )
        if not leaderboard_resp.ok:
            msg = f"Getting leaderboard for {str(key)} failed"
            try:
                logger.error(f"{msg}: {leaderboard_resp.json()}")
            except:
                logger.error(f"{msg}: {leaderboard_resp}")
        leaderboard_json = leaderboard_resp.json()
        leaderboard = SeasonLeaderboard(**leaderboard_json)
        if not leaderboard.players:
            logger.info(f"Leaderboard {str(key)} has no players. Skipping.")
            continue
        else:
            logger.info(f"Found leaderboard for {str(key)}")
        leaderboards[key] = leaderboard.players
    return leaderboards


def summarize_leaderboards(
    leaderboards: dict[LeaderboardKey, list[LeaderboardPlayer]]
) -> dict[str, list[PlayerRank]]:
    players = defaultdict(list)
    for key, leaderboard in leaderboards.items():
        for player in leaderboard:
            players[player.id].append(PlayerRank.from_player(player, key))
    return players


def write_to_cache(cache_path: Path, obj: dict) -> None:
    contents = json.dumps(obj, sort_keys=True, indent=4, separators=(", ", " : "))
    cache_path.write_text(contents, encoding="utf-8")


def read_cache(cache_path: Path) -> Union[dict, list]:
    return json.loads(cache_path.read_text(encoding="utf-8"))


def write_to_redis(players: dict[str, list[dict[str, PlayerRank]]]) -> None:
    logger.info("Writing to redis...")
    redis_client = Redis(
        host=config["REDIS_HOST"],
        port=config["REDIS_PORT"],
        password=config["REDIS_PASSWORD"],
    )
    for account_id, leaderboards in players.items():
        redis_client.set(account_id.replace(".", ":"), json.dumps(leaderboards))


@click.command()
@click.option(
    "-c",
    "--cache-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("./data"),
)
@click.option("--use-cache", is_flag=True)
@click.option("--quick", is_flag=True)
def main(
    cache_dir: Optional[Path],
    use_cache: bool,
    quick: bool,
) -> None:
    """Fetch and summarize PUBG leadersboards and write them to Redis"""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    leaderboards_cache = cache_dir / "leaderboards.json"
    if not quick and use_cache and leaderboards_cache.exists():
        leaderboards = read_cache(leaderboards_cache)
    else:
        leaderboards = get_leaderboards(quick=quick)
        if use_cache:
            write_to_cache(cache_dir / "leanderboards.json", leaderboards)
    player_ranks = summarize_leaderboards(leaderboards)
    player_ranks_json = {
        account_id: [player.model_dump_json() for player in players]
        for account_id, players in player_ranks.items()
    }
    if not quick and use_cache:
        write_to_cache(cache_dir / "players.json", player_ranks_json)
    write_to_redis(player_ranks_json)


if __name__ == "__main__":
    main()
