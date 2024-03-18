from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict


class GameMode(Enum):
    SOLO = "solo"
    SOLO_FPP = "solo-fpp"
    DUO = "duo"
    DUO_FPP = "duo-fpp"
    SQUAD = "squad"
    SQUAD_FPP = "squad-fpp"

    @classmethod
    def current_modes(cls):
        # Only found leaderboards for these game modes
        return (cls.SOLO, cls.SQUAD, cls.SQUAD_FPP)


@dataclass(frozen=True)
class LeaderboardKey:
    platform_region: str
    season: str
    game_mode: GameMode

    def __str__(self):
        return f"{self.season} {self.platform_region} {self.game_mode.value}"


class PubgApiBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )


class SeasonAttributes(PubgApiBase):
    is_current_season: bool = Field(alias="isCurrentSeason")
    is_off_season: bool = Field(alias="isOffseason")


class Season(PubgApiBase):
    id: str
    type: str
    attributes: SeasonAttributes


class PlayerStats(PubgApiBase):
    games: int
    wins: int


class PlayerAttributes(PubgApiBase):
    rank: int
    stats: PlayerStats


class LeaderboardPlayer(PubgApiBase):
    id: str
    attributes: PlayerAttributes


class SeasonLeaderboard(PubgApiBase):
    players: list[LeaderboardPlayer] = Field(alias="included", default_factory=list)


class PlayerRank(BaseModel):
    platform_region: str
    season: str
    game_mode: GameMode
    rank: int
    games_played: int
    wins: int

    @classmethod
    def from_player(cls, player: LeaderboardPlayer, key: LeaderboardKey) -> "PlayerRank":
        attr = player.attributes
        stats = attr.stats
        return cls(
            platfom_region=key.platform_region,
            season=key.season,
            game_mode=key.game_mode,
            rank=attr.rank,
            games_played=stats.games,
            wins=stats.wins,
        )