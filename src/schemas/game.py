from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from sqlmodel import SQLModel

from schemas.theme import ThemeBase


class GameBase(SQLModel):
    theme_id: int
    started_at: datetime
    ended_at: datetime | None = None
    points: int
    round: int
    skip_penalty: bool


class GameListItem(GameBase):
    """For listing"""

    id: int
    theme: ThemeBase | None = None


class TeamStats(BaseModel):
    name: str
    score: int


class GameInfo(BaseModel):
    teams: list[TeamStats]
    current_team_index: int
    current_round: int


class GameDetailsResponse(GameBase):
    """For getting details"""

    id: int
    info: GameInfo
    words_guessed: list[str]
    words_skipped: list[str]

    theme: ThemeBase | None = None


class GameUpsertedResponse(GameBase):
    id: int
    info: GameInfo
    words_guessed: list[str]
    words_skipped: list[str]


class GameCreatePayload(GameBase):
    info: GameInfo


class GameUpdatePayload(BaseModel):
    info: GameInfo
    words_guessed: list[str]
    words_skipped: list[str]
    ended_at: datetime | None = None


class GameOrderBy(StrEnum):
    ID = 'id'
