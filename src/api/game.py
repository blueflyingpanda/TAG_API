import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from dal import apply_games_ordering, get_filtered_games, get_game_details
from db import Game, User, get_db
from schemas import ErrorResponse
from schemas.game import (
    GameCreatePayload,
    GameDetailsResponse,
    GameListItem,
    GameOrderBy,
    GameUpdatePayload,
    GameUpsertedResponse,
)
from utils.oauth import get_current_user

logger = logging.getLogger('api.game')

router = APIRouter(prefix='/games', tags=['Games'])


async def get_game_or_404(db: AsyncSession, game_id: int, user: User) -> Game:
    game = await get_game_details(db, user, game_id)
    if not game:
        logger.error('No such %s: %r', Game, game_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{Game.__name__} with id {game_id} not found'
        )
    return game


@router.get('/', response_model=Page[GameListItem])
async def get_games(
    theme_id: int | None = None,
    ended: bool = False,
    skip_penalty: bool | None = None,
    order: GameOrderBy = GameOrderBy.ID,
    descending: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = await get_filtered_games(user, theme_id, ended, skip_penalty)
    query = await apply_games_ordering(query, order, descending)
    return await paginate(db, query)


@router.get(
    '/{game_id}',
    response_model=GameDetailsResponse,
    responses={404: {'description': 'Game not found', 'model': ErrorResponse}},
)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Game:
    game = await get_game_or_404(db, game_id, user)
    return game


@router.post('/', response_model=GameUpsertedResponse, status_code=201)
async def create_game(
    game: GameCreatePayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> Game:
    game_data = game.model_dump()
    game_record = Game.model_validate(game_data)
    game_record.starter = user

    db.add(game_record)
    await db.commit()
    await db.refresh(game_record)
    return game_record


@router.put(
    '/{game_id}',
    response_model=GameUpsertedResponse,
    responses={404: {'description': 'Game not found', 'model': ErrorResponse}},
)
async def update_game(
    game_id: int,
    game_info: GameUpdatePayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Game:
    game = await get_game_or_404(db, game_id, user)

    game.info = game_info.info.model_dump()

    game.words_guessed = list(set(game.words_guessed + game_info.words_guessed))
    game.words_skipped = list(set(game.words_skipped + game_info.words_skipped))
    game.ended_at = game_info.ended_at

    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game
