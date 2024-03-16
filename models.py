from pydantic import BaseModel, Field, ConfigDict


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
