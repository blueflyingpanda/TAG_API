import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette import status

from dal import get_or_404
from db import Theme, User, get_db
from schemas import ErrorResponse
from schemas.theme import ThemeDetailsResponse, ThemeListItem, ThemePayload
from utils.auth import get_current_user

logger = logging.getLogger('api.theme')

router = APIRouter(prefix='/themes')


@router.get('/', response_model=Page[ThemeListItem])
async def get_themes(db: AsyncSession = Depends(get_db)):
    query = select(Theme).order_by(Theme.id.desc())
    return await paginate(db, query)


@router.get(
    '/{theme_id}',
    response_model=ThemeDetailsResponse,
    responses={404: {'description': 'Theme not found', 'model': ErrorResponse}},
)
async def get_theme(theme_id: int, db: AsyncSession = Depends(get_db)) -> Theme:
    theme = await get_or_404(db, Theme, theme_id)
    await db.refresh(theme, ['creator'])
    return theme


@router.post(
    '/',
    response_model=ThemeDetailsResponse,
    status_code=201,
    responses={409: {'description': 'Theme with this name already exists', 'model': ErrorResponse}},
)
async def create_theme(
    theme: ThemePayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
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
