from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from db import Auth, User


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
