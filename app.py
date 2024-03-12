import requests
from pydantic import BaseModel, Field
import time
import sys
from requests_ratelimiter import LimiterSession
import json
from collections import defaultdict
from dotenv import dotenv_values
import os
import argparse
from pathlib import Path
from typing import Any, Iterable, Optional, Union

config = {
    **dotenv_values(".env"),
}

pretty_config = ', '.join([f'{key}={value}' for key, value in config.items()])
print(f"Using config {pretty_config}")

config |= dotenv_values(".env.secret")

class SeasonAttributes(BaseModel):
    is_current_season: bool = Field(serialization_alias="isCurrentSeason")
    is_off_season: bool = Field(serialization_alias="isOffSeason")

class Season(BaseModel):
    id: str
    type: str
    attributes: SeasonAttributes

headers = {
    "Accept": "application/vnd.api+json",
    "Accept-Encoding": "gzip",
    "User-Agent": "pubg-leader-updater", # TODO: Add version getter here
    "Authorization": f"Bearer {config['PUBG_API_KEY']}",
}

session = LimiterSession(per_minute=9, headers=headers)
platform = "psn"
platform_region = "pc-na"

# game_modes = ("solo","solo-fpp", "duo", "duo-fpp", "squad", "squad-fpp")
game_modes = ("solo", "squad", "squad-fpp") # Only found leaderboards for these
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
    "console": ["psn", "xbox"]
}

seasons_url = "https://api.pubg.com/shards/{shard}/seasons" # This should be cached by the month
leaderboard_url = "https://api.pubg.com/shards/{shard}/leaderboards/{season_id}/{game_mode}" # TODO format this properly


def iter_platform_regions() -> Iterable[str]:
    for base, regions in platform_regions.items():
        for region in regions:
            yield f"{base}-{region}"


def get_current_season(shard: str) -> Optional[str]:
    seasons_resp = session.get(seasons_url.format(shard=shard), headers=headers)
    if not seasons_resp.ok:
        print(f"{shard} failed")
        print(seasons_resp)
        return None
    for season in seasons_resp.json()["data"]:
        attr = season["attributes"]
        if attr["isCurrentSeason"]:
            print(f"Platform {shard} season {season['id']}")
            return season["id"]
    return None


def iter_leaderboards() -> Iterable[tuple[str, str, str]]:
    for platform_region in iter_platform_regions():
        if current_season := get_current_season(platform_region):
            for game_mode in game_modes:
                yield platform_region, current_season, game_mode

def get_leaderboards() -> dict[str, Any]:
    leaderboards = {}
    for platform_region, current_season, game_mode in iter_leaderboards():
        leaderboard_resp = session.get(leaderboard_url.format(shard=platform_region, season_id=current_season, game_mode=game_mode), headers=headers)
        if not leaderboard_resp.ok:
            try:
                print(leaderboard_resp.json())
            except:
                print(leaderboard_resp)
        leaderboard_json = leaderboard_resp.json()
        leaderboard = leaderboard_json.get("included", [])
        log_key = f"{platform_region} {game_mode}"
        if not leaderboard:
            print(f"Skipping {log_key}")
            continue
        else:
            print(f"\nFOUND {log_key}\n")
        key = f"{platform_region} {current_season} {game_mode}"
        leaderboards[key] = leaderboard
    return leaderboards



def summarize_leaderboards(leaderboards: dict[str, Any]) -> dict:
    players = defaultdict(list)
    for key, leaderboard in leaderboards.items():
        platform_region, current_season, game_mode = key.split(" ")
        for player in leaderboard:
            attr = player["attributes"]
            stats = attr["stats"]
            player_data = {
                "platform_region": platform_region,
                "current_season": current_season,
                "game_mode": game_mode,
                "rank": attr["rank"],
                "games_played": stats["games"],
                "wins": stats["wins"]
            }
            players[player["id"]].append(player_data)
    return players

def write_to_cache(cache_path: Path, obj: dict) -> None:
    contents = json.dumps(obj, sort_keys=True, indent=4, separators = (". ", " = "))
    cache_path.write_text(contents, encoding="utf-8")

def read_cache(cache_path: Path) -> Union[dict, list]:
    return json.loads(cache_path.read_text(encoding="utf-8"))

def main(cache_dir: Optional[Path]=Path("./data"), use_cache: bool=False) -> None:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    leaderboards_cache = cache_dir / "leaderboards.json"
    if use_cache and leaderboards_cache.exists():
        leaderboards = read_cache(leaderboards_cache)
    else:
        # disable using future caching
        use_cache = False
        leaderboards = get_leaderboards()
        write_to_cache(cache_dir, "leanderboards.json", leaderboards)
    players = summarize_leaderboards(leaderboards)
    write_to_cache(cache_dir, "players.json", players)

def parse_args() -> dict[str, Any]:
    parser = argparse.ArgumentParser(prog='PubgLeaderboard', description='Scrape and consolidate the PUBg leaderboards')
    parser.add_argument("-c", "--cache-dir", help="path to the cache directory", default="./data")
    parser.add_argument("--use-cache", action="store_true")
    args = parser.parse_args()
    return vars(args)

if __name__ == "__main__":
    args = parse_args()
    main(**args)