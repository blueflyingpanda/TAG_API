from datetime import datetime

from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=255)
    email: str = Field(max_length=255)


class UserRead(SQLModel):
    id: int
    username: str
    email: str
    admin: bool
    created_at: datetime
    last_login: datetime | None


class ThemeCreate(SQLModel):
    name: str = Field(max_length=255)
    description: dict | None = None
    public: bool = Field(default=False)
    language: str = Field(default='en', max_length=2)
    difficulty: int = Field(default=1, ge=1, le=5)


class ThemeRead(SQLModel):
    id: int
    name: str
    description: dict | None
    played_count: int
    public: bool
    verified: bool
    language: str
    difficulty: int
    created_at: datetime


class GameCreate(SQLModel):
    theme_id: int
    points: int
    round: int = Field(default=30)
    skip_penalty: bool = Field(default=True)


class GameRead(SQLModel):
    id: int
    theme_id: int | None
    started_by: int | None
    started_at: datetime
    ended_at: datetime | None
    points: int
    round: int
    skip_penalty: bool
    words_guessed: list
    words_skipped: list
