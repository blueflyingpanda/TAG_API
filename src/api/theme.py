import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BeforeValidator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from dal import add_to_favourite, get_filtered_themes, get_theme_details, remove_from_favourite
from db import Theme, User, get_db
from schemas import ErrorResponse
from schemas.theme import ThemeCreatePayload, ThemeDetailsResponse, ThemeListItem, ThemeUpdatePayload
from utils.oauth import get_current_user
from validators import validate_language_alpha2

logger = logging.getLogger('api.theme')

router = APIRouter(prefix='/themes', tags=['Themes'])

LanguageParam = Annotated[str | None, BeforeValidator(validate_language_alpha2)]


async def get_theme_or_404(db: AsyncSession, theme_id: int, user: User) -> Theme:
    theme = await get_theme_details(db, user, theme_id)
    if not theme:
        logger.error('No such %s: %r', Theme, theme_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{Theme.__name__} with id {theme_id} not found'
        )
    return theme


@router.get('/', response_model=Page[ThemeListItem])
async def get_themes(
    language: LanguageParam = None,
    difficulty: int | None = Query(None, ge=1, le=5),
    name: str | None = Query(None, max_length=255),
    mine: bool = False,
    verified: bool = True,
    favourites: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = await get_filtered_themes(user, language, difficulty, name, mine, verified, favourites)
    return await paginate(db, query)


@router.get(
    '/{theme_id}',
    response_model=ThemeDetailsResponse,
    responses={404: {'description': 'Theme not found', 'model': ErrorResponse}},
)
async def get_theme(
    theme_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> ThemeDetailsResponse:
    theme = await get_theme_or_404(db, theme_id, user)
    return ThemeDetailsResponse.model_validate(
        theme, update={'likes': len(theme.favourited_by), 'favourite': user in theme.favourited_by}
    )


@router.post(
    '/',
    response_model=ThemeDetailsResponse,
    status_code=201,
    responses={409: {'description': 'Theme with this name already exists', 'model': ErrorResponse}},
)
async def create_theme(
    theme: ThemeCreatePayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> Theme:
    theme_record = Theme.model_validate(
        theme,
        update={'description': theme.description.model_dump()},
    )
    theme_record.creator = user

    try:
        db.add(theme_record)
        await db.commit()
        await db.refresh(theme_record)
        return theme_record
    except IntegrityError as e:
        logger.error('Could not create new theme: %s', e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f'Theme with name {theme.name} already exists'
        ) from e


@router.put(
    '/{theme_id}',
    response_model=ThemeDetailsResponse,
    responses={404: {'description': 'Theme not found', 'model': ErrorResponse}},
)
async def update_theme(
    theme_id: int,
    theme_info: ThemeUpdatePayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThemeDetailsResponse:
    theme = await get_theme_or_404(db, theme_id, user)
    theme.public = theme_info.public

    db.add(theme)
    await db.commit()
    await db.refresh(theme)

    return ThemeDetailsResponse.model_validate(
        theme, update={'likes': len(theme.favourited_by), 'favourite': user in theme.favourited_by}
    )


@router.post('/{theme_id}/favourite', status_code=status.HTTP_204_NO_CONTENT)
async def add_theme_to_favourites(
    theme_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    theme = await get_theme_or_404(db, theme_id, user)

    await add_to_favourite(db, user, theme)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete('/{theme_id}/favourite', status_code=status.HTTP_204_NO_CONTENT)
async def remove_theme_from_favourites(
    theme_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    theme = await get_theme_or_404(db, theme_id, user)

    await remove_from_favourite(db, user, theme)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
