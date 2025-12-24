from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi_pagination import add_pagination
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from api import auth, game, theme
from cache import close_cache, init_cache
from db import get_db
from errors import AuthError
from log import init_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_logging()
    await init_cache()
    yield
    # Shutdown
    await close_cache()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://blueflyingpanda.github.io'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(theme.router)
app.include_router(game.router)

add_pagination(app)


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={'detail': str(exc)},
    )


@app.get('/ping')
async def ping(db: AsyncSession = Depends(get_db)):
    await db.execute(text('SELECT 1'))
    return {'ping': 'pong'}
