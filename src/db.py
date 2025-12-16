from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Field, Relationship, SQLModel

from conf import settings
from schemas.theme import ThemeBase
from schemas.user import UserBase


class DbModel(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={'nullable': False, 'server_default': func.now()},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={'nullable': False, 'server_default': func.now(), 'onupdate': func.now()},
    )


class User(DbModel, UserBase, table=True):
    __tablename__ = 'users'

    email: str = Field(max_length=255, unique=True, index=True)

    last_login: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    auth: Auth = Relationship(back_populates='user', sa_relationship_kwargs={'uselist': False})

    themes: list[Theme] = Relationship(back_populates='creator')
    games: list[Game] = Relationship(back_populates='starter')


class Auth(DbModel, table=True):
    __tablename__ = 'auths'

    user_id: int = Field(foreign_key='users.id', unique=True)
    user: User = Relationship(back_populates='auth', sa_relationship_kwargs={'uselist': False})

    access_token: str | None
    refresh_token: str | None
    id_token: str | None

    aux_token: str | None


class Theme(DbModel, ThemeBase, table=True):
    __tablename__ = 'themes'

    name: str = Field(max_length=255, unique=True, index=True)
    description: dict | None = Field(default=None, sa_column=Column(JSONB))
    played_count: int = Field(default=0)
    last_played: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
    created_by: int | None = Field(default=None, foreign_key='users.id')
    public: bool = Field(default=False)
    verified: bool = Field(default=False)

    creator: User | None = Relationship(back_populates='themes')
    games: list[Game] = Relationship(back_populates='theme')


class Game(DbModel, table=True):
    __tablename__ = 'games'

    theme_id: int | None = Field(default=None, foreign_key='themes.id')
    started_by: int | None = Field(default=None, foreign_key='users.id')
    started_at: datetime = Field(sa_type=DateTime(timezone=True))
    ended_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
    info: dict | None = Field(default=None, sa_column=Column(JSONB))
    points: int
    round: int = Field(default=30)
    skip_penalty: bool = Field(default=True)
    words_guessed: list = Field(default_factory=list, sa_column=Column(JSONB))
    words_skipped: list = Field(default_factory=list, sa_column=Column(JSONB))

    # Relationships
    theme: Theme | None = Relationship(back_populates='games')
    starter: User | None = Relationship(back_populates='games')


DATABASE_URL = f'postgresql+asyncpg://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}'
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session
