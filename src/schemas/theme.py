from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel

from schemas.user import UserBase
from validators import validate_language_alpha2


class ThemeDescription(BaseModel):
    words: list[str]
    teams: list[str]

    @field_validator('words')
    @classmethod
    def validate_words(cls, v: list[str]) -> list[str]:
        if len(v) < 100:
            raise ValueError('At least 100 words are required')
        return v

    @field_validator('teams')
    @classmethod
    def validate_teams(cls, v: list[str]) -> list[str]:
        if len(v) < 10:
            raise ValueError('At least 10 teams are required')
        return v


class ThemeBase(SQLModel):
    name: str = Field(max_length=255)
    language: str = Field(default='en', max_length=2)  # ISO 639 alpha-2
    difficulty: int = Field(default=1, ge=1, le=5)
    verified: bool = False

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        return validate_language_alpha2(v)


class ThemeDetailsResponse(ThemeBase):
    id: int
    public: bool
    description: ThemeDescription
    played_count: int = 0
    last_played: datetime | None = None
    creator: UserBase
    likes: int = 0
    favourite: bool = False


class ThemeListItem(ThemeBase):
    """For listing"""

    id: int


class ThemeCreatePayload(ThemeBase):
    """For theme creation"""

    description: ThemeDescription
    public: bool = False


class ThemeUpdatePayload(BaseModel):
    """For theme update"""

    public: bool = False


class ThemeOrderBy(StrEnum):
    ID = 'id'
    NAME = 'name'
    PLAYED_COUNT = 'played_count'
    LAST_PLAYED = 'last_played'
    LIKES = 'likes'
