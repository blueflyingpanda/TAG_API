import logging
from datetime import UTC, datetime

from sqlalchemy import Select, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import asc, desc, or_, select

from db import Auth, Game, Theme, User, UserToFavouriteThemes
from schemas.game import GameOrderBy
from schemas.theme import ThemeOrderBy

logger = logging.getLogger('dal')


async def get_or_create_user(id_token_payload: dict, db: AsyncSession) -> User:
    email = id_token_payload['email']

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)

    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            picture=id_token_payload.get('picture'),
            last_login=datetime.now(UTC),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def update_or_create_auth(user: User, db: AsyncSession, id_token: str, access_token: str) -> Auth:
    stmt = select(Auth).where(Auth.user_id == user.id)
    result = await db.execute(stmt)
    auth = result.scalar_one_or_none()

    if auth:
        auth.id_token = id_token
        auth.access_token = access_token
        auth.updated_at = datetime.now(UTC)
    else:
        auth = Auth(user=user, id_token=id_token, access_token=access_token)
        db.add(auth)

    await db.commit()
    await db.refresh(auth)
    return auth


async def get_theme_details(db: AsyncSession, user: User, theme_id: int) -> Theme:
    query = await get_available_themes(user)
    result = await db.execute(
        query.where(Theme.id == theme_id).options(selectinload(Theme.creator), selectinload(Theme.favourited_by))
    )
    instance = result.scalar_one_or_none()

    return instance


async def get_game_details(db: AsyncSession, user: User, game_id: int) -> Game:
    result = await db.execute(
        select(Game)
        .where(Game.id == game_id, Game.starter == user)
        .options(selectinload(Game.starter), selectinload(Game.theme))
    )
    instance = result.scalar_one_or_none()

    return instance


async def get_available_themes(user: User) -> Select[Theme]:
    if user.admin:
        return select(Theme)
    return select(Theme).where(or_(Theme.public, Theme.creator == user))


async def apply_themes_ordering(
    query: Select[Theme],
    order_by: ThemeOrderBy = ThemeOrderBy.ID,
    descending: bool = False,
) -> Select[Theme]:
    order_func = desc if descending else asc

    match order_by:
        case ThemeOrderBy.ID:
            query = query.order_by(order_func(Theme.id))
        case ThemeOrderBy.NAME:
            query = query.order_by(order_func(Theme.name))
        case ThemeOrderBy.PLAYED_COUNT:
            query = query.order_by(order_func(Theme.played_count))
        case ThemeOrderBy.LAST_PLAYED:
            if descending:
                query = query.order_by(Theme.last_played.desc().nulls_last())
            else:
                query = query.order_by(Theme.last_played.asc().nulls_last())
        case ThemeOrderBy.LIKES:
            likes_count = (
                select(func.count(UserToFavouriteThemes.user_id))
                .where(UserToFavouriteThemes.theme_id == Theme.id)
                .correlate(Theme)
                .scalar_subquery()
            )
            query = query.order_by(order_func(likes_count))

    return query


async def get_filtered_themes(
    user: User,
    language: str | None,
    difficulty: int | None,
    name: str | None,
    mine: bool,
    verified: bool,
    favourites: bool,
) -> Select[Theme]:
    query = select(Theme)

    if mine:
        query = query.where(Theme.creator == user)
    else:
        query = await get_available_themes(user)

    if verified:
        query = query.where(Theme.verified)

    if favourites:
        query = query.join(UserToFavouriteThemes).where(UserToFavouriteThemes.user_id == user.id)

    if language is not None:
        query = query.where(Theme.language == language)
    if difficulty is not None:
        query = query.where(Theme.difficulty == difficulty)
    if name is not None:
        query = query.where(Theme.name.ilike(f'%{name}%'))

    return query


async def add_to_favourite(db: AsyncSession, user: User, theme: Theme):
    stmt = insert(UserToFavouriteThemes).values(user_id=user.id, theme_id=theme.id).on_conflict_do_nothing()

    await db.execute(stmt)
    await db.commit()


async def remove_from_favourite(db: AsyncSession, user: User, theme: Theme):
    stmt = delete(UserToFavouriteThemes).where(
        UserToFavouriteThemes.user_id == user.id, UserToFavouriteThemes.theme_id == theme.id
    )

    await db.execute(stmt)
    await db.commit()


async def get_filtered_games(
    user: User,
    theme_id: int | None = None,
    ended: bool = False,
    skip_penalty: bool | None = None,
) -> Select[Game]:
    query = select(Game).where(Game.starter == user).options(selectinload(Game.theme))

    if theme_id is not None:
        query = query.where(Game.theme_id == theme_id)
    if ended:
        query = query.where(Game.ended_at is not None)
    if skip_penalty is not None:
        query = query.where(Game.skip_penalty == skip_penalty)

    return query


async def apply_games_ordering(
    query: Select[Game],
    order_by: GameOrderBy = GameOrderBy.ID,
    descending: bool = False,
) -> Select[Game]:
    order_func = desc if descending else asc

    match order_by:
        case GameOrderBy.ID:
            query = query.order_by(order_func(Game.id))

    return query
