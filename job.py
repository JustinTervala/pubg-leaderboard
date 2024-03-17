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

from config import load_config, configure_logging
from models import Season, SeasonLeaderboard


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
platform = "psn"
platform_region = "pc-na"

# game_modes = ("solo","solo-fpp", "duo", "duo-fpp", "squad", "squad-fpp")
game_modes = ("solo", "squad", "squad-fpp")  # Only found leaderboards for these
platforms = ("kakao", "stadia", "steam", "psn", "xbox", "console")
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


def iter_leaderboards() -> Iterable[tuple[str, str, str]]:
    for platform_region in iter_platform_regions():
        if current_season := get_current_season(platform_region):
            for game_mode in game_modes:
                yield platform_region, current_season, game_mode


def get_leaderboards(quick: bool = False) -> dict[str, Any]:
    leaderboards = {}
    i = 0
    logger.info("Scraping leaderboards...")
    out = []
    for platform_region, current_season, game_mode in iter_leaderboards():
        log_key = f"{current_season} {platform_region} {game_mode}"
        i += 1
        if quick and i > 3:
            logger.info("ENDING")
            break
        leaderboard_resp = session.get(
            leaderboard_url.format(
                shard=platform_region, season_id=current_season, game_mode=game_mode
            ),
            headers=headers,
        )
        if not leaderboard_resp.ok:
            try:
                logger.error(
                    f"Getting leaderboard for {log_key} failed: {leaderboard_resp.json()}"
                )
            except:
                logger.error(
                    f"Getting leaderboard for {log_key} failed: {leaderboard_resp}"
                )
        leaderboard_json = leaderboard_resp.json()
        leaderboard = SeasonLeaderboard(**leaderboard_json)
        if not leaderboard.players:
            logger.info(f"Leaderboard {log_key} has no players. Skipping.")
            continue
        else:
            logger.info(f"Found leaderboard for {log_key}")
        key = (platform_region, current_season, game_mode)
        leaderboards[key] = leaderboard.players
    return leaderboards


def summarize_leaderboards(leaderboards: dict[str, Any]) -> dict:
    players = defaultdict(list)
    for (
        platform_region,
        current_season,
        game_mode,
    ), leaderboard in leaderboards.items():
        for player in leaderboard:
            attr = player.attributes
            stats = attr.stats
            player_data = {
                "platform_region": platform_region,
                "current_season": current_season,
                "game_mode": game_mode,
                "rank": attr.rank,
                "games_played": stats.games,
                "wins": stats.wins,
            }
            players[player.id].append(player_data)
    return players


def write_to_cache(cache_path: Path, obj: dict) -> None:
    contents = json.dumps(obj, sort_keys=True, indent=4, separators=(", ", " : "))
    cache_path.write_text(contents, encoding="utf-8")


def read_cache(cache_path: Path) -> Union[dict, list]:
    return json.loads(cache_path.read_text(encoding="utf-8"))


def write_to_redis(players: dict[str, list[dict]]) -> None:
    logger.info("Writing to redis...")
    redis_client = Redis(
        host=config["REDIS_ADDRESS"],
        port=config["REDIS_PORT"],
        password=config["REDIS_PASSWORD"],
    )
    for i, (account_id, leaderboards) in enumerate(players.items()):
        if i > 10:
            break
        redis_client.set(account_id.replace(".", ":"), json.dumps(leaderboards))


def main(
    cache_dir: Optional[Path] = Path("./data"),
    use_cache: bool = False,
    quick: bool = False,
) -> None:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    leaderboards_cache = cache_dir / "leaderboards.json"
    if not quick and use_cache and leaderboards_cache.exists():
        leaderboards = read_cache(leaderboards_cache)
    else:
        # disable using future caching
        use_cache = False
        leaderboards = get_leaderboards(quick=quick)
        if use_cache:
            write_to_cache(cache_dir / "leanderboards.json", leaderboards)
    players = summarize_leaderboards(leaderboards)
    if not quick:
        write_to_cache(cache_dir / "players.json", players)
    # write_to_redis(players)


def parse_args() -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="PubgLeaderboard",
        description="Scrape and consolidate the PUBg leaderboards",
    )
    parser.add_argument(
        "-c", "--cache-dir", help="path to the cache directory", default="./data"
    )
    parser.add_argument("--use-cache", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    args = parse_args()
    main(**args)
