import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from auth import generate_aux_token, generate_oauth_redirect_uri, verify_id_token
from cache import get_cache
from conf import settings
from dal import get_or_create_user, update_or_create_auth
from db import get_db

router = APIRouter(prefix='/auth')


class TokenPayload(BaseModel):
    code: str
    state: str
    nonce: str


class TokenResponse(BaseModel):
    id_token: str


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
    response = RedirectResponse(settings.fe_url, status_code=302)

    response.set_cookie(
        key='auth_token',
        value=aux_token,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=True,  # Only sent over HTTPS (set to False for local dev)
        samesite='lax',  # CSRF protection (use "strict" for more security or "none" for cross-site)
        max_age=settings.jwt_expires_in_days * 3600 * 7,  # Cookie expiration in seconds
        path='/',  # Cookie available for entire domain
    )

    return response
