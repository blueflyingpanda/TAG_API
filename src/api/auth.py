import secrets

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette.responses import RedirectResponse

from cache import get_cache
from conf import settings
from dal import get_or_create_user, update_or_create_auth
from db import User, get_db
from schemas import UserRead
from utils.auth import generate_aux_token, generate_oauth_redirect_uri, verify_aux_token, verify_id_token

router = APIRouter(prefix='/auth')


class CodePayload(BaseModel):
    code: str


class TokenResponse(BaseModel):
    token: str


@router.get('/login')
async def login(redis: Redis = Depends(get_cache)):
    uri = await generate_oauth_redirect_uri(redis)
    return RedirectResponse(uri, status_code=302)


@router.get('/token')
async def token(code: str, state: str, redis: Redis = Depends(get_cache), db: AsyncSession = Depends(get_db)):
    token_url = 'https://oauth2.googleapis.com/token'

    nonce = await redis.get(f'oauth:state:{state}')

    if not nonce:
        raise HTTPException(status_code=400, detail='Invalid state')

    await redis.delete(f'oauth:state:{state}')

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                'code': code,
                'state': state,
                'client_id': settings.oauth_gcloud_id,
                'client_secret': settings.oauth_gcloud_secret,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.oauth_redirect_uri,
            },
        )

        response.raise_for_status()
        data = response.json()

    id_token = data['id_token']
    access_token = data['access_token']
    refresh_token = data.get('refresh_token', '')

    id_token_payload = await verify_id_token(id_token, expected_nonce=nonce)

    user = await get_or_create_user(id_token_payload, db)

    aux_token = await generate_aux_token(user)

    await update_or_create_auth(user, db, id_token, access_token, refresh_token, aux_token)

    exchange_code = secrets.token_urlsafe(32)

    await redis.setex(f'auth:exchange:{exchange_code}', 60, aux_token)

    return RedirectResponse(f'{settings.fe_url}?code={exchange_code}', status_code=302)


@router.post('/exchange')
async def exchange_token(body: CodePayload, redis: Redis = Depends(get_cache)) -> TokenResponse:
    """Exchange one-time code for auth token"""
    code = body.code
    aux_token = await redis.get(f'auth:exchange:{code}')

    if not aux_token:
        raise HTTPException(status_code=400, detail='Invalid or expired code')

    await redis.delete(f'auth:exchange:{code}')

    return TokenResponse(token=aux_token)


async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get current authenticated user from Bearer token"""
    if not authorization:
        raise HTTPException(status_code=401, detail='Not authenticated')

    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Invalid authentication scheme')

    token = authorization.replace('Bearer ', '')

    payload = verify_aux_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid or expired token')

    stmt = select(User).where(User.id == payload['user_id'])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    return user


@router.get('/me')
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
