from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Field, Relationship, SQLModel

from conf import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER


class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    admin: bool = Field(default=False)
    username: str = Field(max_length=64, unique=True, index=True)
    password: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True, index=True)
    last_login: datetime | None = None

    themes: list[Theme] = Relationship(back_populates='creator')
    games: list[Game] = Relationship(back_populates='starter')


class Theme(SQLModel, table=True):
    __tablename__ = 'theme'

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    name: str = Field(max_length=255, unique=True, index=True)
    description: dict | None = Field(default=None, sa_column=Column(JSONB))
    played_count: int = Field(default=0)
    last_played: datetime | None = None
    created_by: int | None = Field(default=None, foreign_key='users.id')
    public: bool = Field(default=False)
    verified: bool = Field(default=False)
    language: str = Field(default='en', max_length=2)  # ISO 639 alpha-2
    difficulty: int = Field(default=1, ge=1, le=5)

    creator: User | None = Relationship(back_populates='themes')
    games: list[Game] = Relationship(back_populates='theme')


class Game(SQLModel, table=True):
    __tablename__ = 'game'

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    theme_id: int | None = Field(default=None, foreign_key='theme.id')
    started_by: int | None = Field(default=None, foreign_key='users.id')
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    info: dict | None = Field(default=None, sa_column=Column(JSONB))
    points: int
    round: int = Field(default=30)
    skip_penalty: bool = Field(default=True)
    words_guessed: list = Field(default_factory=list, sa_column=Column(JSONB))
    words_skipped: list = Field(default_factory=list, sa_column=Column(JSONB))

    # Relationships
    theme: Theme | None = Relationship(back_populates='games')
    starter: User | None = Relationship(back_populates='games')


DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session
