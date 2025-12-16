from datetime import datetime

import pycountry
from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel

from schemas.user import UserBase


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

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate compliance with ISO 639-1 alpha-2 codes ('en', 'ru' ...)"""
        lang = v.lower()
        try:
            pycountry.languages.get(alpha_2=lang)
            return lang
        except (KeyError, AttributeError) as e:
            raise ValueError(f'Invalid ISO 639-1 language code: {lang}') from e


class ThemeDetailsResponse(ThemeBase):
    id: int
    description: ThemeDescription
    played_count: int = 0
    last_played: datetime | None = None
    creator: UserBase


class ThemeListItem(ThemeBase):
    """For listing"""

    id: int


class ThemePayload(ThemeBase):
    """For theme creation"""

    description: ThemeDescription
