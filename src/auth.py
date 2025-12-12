import secrets
import urllib.parse
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from jwt import PyJWKClient
from redis.asyncio import Redis

from conf import settings
from db import User


async def generate_oauth_redirect_uri(redis: Redis) -> str:
    state = secrets.token_urlsafe(64)
    nonce = secrets.token_urlsafe(64)

    await redis.setex(f'oauth:state:{state}', timedelta(minutes=5), nonce)

    query_params = {
        'client_id': settings.oauth_gcloud_id,
        'redirect_uri': settings.oauth_redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(('openid', 'profile', 'email')),
        'state': state,
        'nonce': nonce,
    }
    base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)

    return f'{base_url}?{query_string}'


async def verify_id_token(id_token: str, expected_nonce: str) -> dict:
    """Verify Google ID token signature and nonce"""

    # Get the signing key from Google's JWKS endpoint
    jwks_url = 'https://www.googleapis.com/oauth2/v3/certs'
    jwks_client = PyJWKClient(jwks_url)

    # Get the signing key from the token header
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)

    payload = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=['RS256'],
        audience=settings.oauth_gcloud_id,
        options={
            'verify_signature': True,
            'verify_aud': True,
            'verify_exp': True,
        },
    )

    if payload.get('nonce') != expected_nonce:
        raise HTTPException(status_code=400, detail='Nonce mismatch - potential replay attack')

    if payload.get('iss') not in ['https://accounts.google.com', 'accounts.google.com']:
        raise HTTPException(status_code=400, detail='Invalid issuer')

    return payload


async def generate_aux_token(user: User) -> str:
    """Generates auxiliary token for FE needs."""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'picture': user.picture,
        'admin': user.admin,
        'exp': datetime.now(UTC) + timedelta(days=settings.jwt_expires_in_days),
        'iat': datetime.now(UTC),
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_aux_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
