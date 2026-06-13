import logging
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from cache import get_cache
from conf import settings
from dal import get_or_create_telegram_user, get_or_create_user, update_or_create_auth
from db import get_db
from errors import AuthError
from schemas import ErrorResponse
from utils.oauth import generate_aux_token, generate_oauth_redirect_uri, verify_id_token, verify_telegram_init_data

logger = logging.getLogger('api.auth')

router = APIRouter(prefix='/auth', tags=['Authorization'])


class CodePayload(BaseModel):
    code: str


class TokenResponse(BaseModel):
    token: str


@router.get('/login', responses={302: {'description': 'Redirect to Google OAuth login'}})
async def login(redirect_uri: str | None = None, cache: Redis = Depends(get_cache)):
    """
    Request comes from FE to init login process via oauth2.0 and open id connect.
    FE is redirected to selection of Google account.

    Mobile clients pass ?redirect_uri=tag://auth (allowlisted) to receive
    the exchange code via deep link instead of the web FE redirect.
    """
    if redirect_uri is not None and redirect_uri != settings.mobile_redirect_uri:
        raise HTTPException(status_code=400, detail='Invalid redirect_uri')

    uri = await generate_oauth_redirect_uri(cache, final_redirect_uri=redirect_uri)
    return RedirectResponse(uri, status_code=302)


@router.get(
    '/token',
    responses={
        302: {'description': 'Redirect to frontend with exchange code'},
        401: {'description': 'Invalid state/nonce parameter or invalid cert issuer', 'model': ErrorResponse},
    },
)
async def token(code: str, state: str, cache: Redis = Depends(get_cache), db: AsyncSession = Depends(get_db)):
    """
    After user has chosen a Google account, Google redirects us to BE
    with the code that can be exchanged for access, refresh and id tokens.
    From id token BE creates its own aux token to identify a user from FE.
    Then redirects to FE with the code that can be exchanged for aux token.
    """
    token_url = 'https://oauth2.googleapis.com/token'

    nonce = await cache.get(f'oauth:state:{state}')

    if not nonce:
        logger.error('No nonce for %s', state)
        raise HTTPException(status_code=401, detail='Invalid state')

    await cache.delete(f'oauth:state:{state}')

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

    try:
        id_token_payload = await verify_id_token(id_token, expected_nonce=nonce)
    except AuthError as e:
        logger.error('Could not verify id_token: %s', e)
        raise

    user = await get_or_create_user(id_token_payload, db)

    await update_or_create_auth(user, db, id_token, access_token)

    exchange_code = secrets.token_urlsafe(32)
    aux_token = await generate_aux_token(user)
    await cache.setex(f'auth:exchange:{exchange_code}', 60, aux_token)

    # Mobile clients registered a deep-link redirect during /login
    final_redirect = await cache.get(f'oauth:redirect:{state}')
    await cache.delete(f'oauth:redirect:{state}')
    if final_redirect:
        if isinstance(final_redirect, bytes):
            final_redirect = final_redirect.decode()
        return RedirectResponse(f'{final_redirect}?code={exchange_code}', status_code=302)

    return RedirectResponse(f'{settings.fe_url}?code={exchange_code}', status_code=302)


class TelegramPayload(BaseModel):
    init_data: str


@router.post(
    '/telegram',
    responses={401: {'description': 'Invalid or expired initData', 'model': ErrorResponse}},
)
async def telegram_login(body: TelegramPayload, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate via Telegram Mini App initData."""
    try:
        tg_user = verify_telegram_init_data(body.init_data)
    except AuthError as e:
        logger.error('Telegram auth failed: %s', e)
        raise

    user = await get_or_create_telegram_user(tg_user, db)
    aux_token = await generate_aux_token(user)

    return TokenResponse(token=aux_token)


@router.post(
    '/exchange',
    responses={400: {'description': 'Invalid code', 'model': ErrorResponse}},
)
async def exchange_token(body: CodePayload, cache: Redis = Depends(get_cache)) -> TokenResponse:
    """Exchange one-time code for aux token"""
    code = body.code
    aux_token = await cache.get(f'auth:exchange:{code}')

    if not aux_token:
        logger.error('No aux token for %s', code)
        raise HTTPException(status_code=400, detail='Invalid or expired code')

    await cache.delete(f'auth:exchange:{code}')

    return TokenResponse(token=aux_token)
