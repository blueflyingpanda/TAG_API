from enum import StrEnum

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel

from schemas.user import UserBase
from validators import validate_language_alpha2


class WordInfo(BaseModel):
    difficulty: int = Field(ge=1, le=5)


class ThemeDescription(BaseModel):
    words: dict[str, WordInfo]
    teams: list[str]

    @field_validator('words')
    @classmethod
    def validate_words(cls, v: dict[str, WordInfo]) -> dict[str, WordInfo]:
        easy_count = sum(1 for w in v.values() if w.difficulty == 1)
        if easy_count < 30:
            raise ValueError('At least 30 words with difficulty 1 are required')
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
    verified: bool = False

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        return validate_language_alpha2(v)


class ThemeDetailsResponse(ThemeBase):
    id: int
    public: bool
    description: ThemeDescription
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
    LIKES = 'likes'
