from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from cache import close_cache, init_cache
from router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_cache()
    yield
    # Shutdown
    await close_cache()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://blueflyingpanda.github.io'],  # or ['*'] for dev
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)


@app.get('/ping')
async def ping():
    return {'ping': 'pong'}
