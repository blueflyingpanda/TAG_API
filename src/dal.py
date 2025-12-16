import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette import status

from db import Auth, DbModel, User

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


async def update_or_create_auth(
    user: User, db: AsyncSession, id_token: str, access_token: str, refresh_token: str, aux_token: str
) -> Auth:
    stmt = select(Auth).where(Auth.user_id == user.id)
    result = await db.execute(stmt)
    auth = result.scalar_one_or_none()

    if auth:
        auth.id_token = id_token
        auth.access_token = access_token
        auth.refresh_token = refresh_token
        auth.aux_token = aux_token
        auth.updated_at = datetime.now(UTC)
    else:
        auth = Auth(
            user=user, id_token=id_token, access_token=access_token, refresh_token=refresh_token, aux_token=aux_token
        )
        db.add(auth)

    await db.commit()
    await db.refresh(auth)
    return auth


async def get_or_404(db: AsyncSession, model: type[DbModel], record_id: int) -> DbModel:
    """Get an instance by ID or raise 404"""
    instance = await db.get(model, record_id)
    if not instance:
        logger.error('No such %s: %r', model, record_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{model.__name__} with id {record_id} not found'
        )
    return instance
