import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BeforeValidator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette import status
from starlette.responses import Response

from analytics import track
from dal import (
    add_to_favourite,
    apply_themes_ordering,
    get_filtered_themes,
    get_likes_counts,
    get_theme_details,
    remove_from_favourite,
)
from db import CoverImage, Theme, User, get_db
from errors import AuthError
from images import (
    COVER_HEIGHT,
    COVER_WIDTH,
    UPLOAD_MAX_BYTES,
    InvalidImageError,
    delete_cover_file,
    make_cover,
    save_cover,
)
from schemas import ErrorResponse
from schemas.theme import (
    ThemeCreatePayload,
    ThemeDetailsResponse,
    ThemeListItem,
    ThemeOrderBy,
    ThemeUpdatePayload,
    ThemeVisibilityPayload,
)
from utils.oauth import get_current_user, get_optional_user
from validators import validate_language_alpha2

logger = logging.getLogger('api.theme')

router = APIRouter(prefix='/themes', tags=['Themes'])

LanguageParam = Annotated[str | None, BeforeValidator(validate_language_alpha2)]


async def is_cover_used_by_other_themes(db: AsyncSession, cover_id: int, theme_id: int) -> bool:
    # Lock cover row until commit so concurrent droppers of same cover serialize
    await db.exec(select(CoverImage.id).where(CoverImage.id == cover_id).with_for_update())
    result = await db.exec(select(Theme.id).where(Theme.cover_image_id == cover_id, Theme.id != theme_id).limit(1))
    return result.first() is not None


async def get_theme_or_404(db: AsyncSession, theme_id: int, user: User | None) -> Theme:
    theme = await get_theme_details(db, user, theme_id)
    if not theme:
        logger.error('No such %s: %r', Theme, theme_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{Theme.__name__} with id {theme_id} not found'
        )
    return theme


async def get_theme_for_update_or_404(db: AsyncSession, theme_id: int, user: User) -> Theme:
    theme = await get_theme_or_404(db, theme_id, user)

    if not user.admin and theme.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{Theme.__name__} with id {theme_id} cannot be changed by user {user.id}',
        )

    return theme


@router.get('/', response_model=Page[ThemeListItem])
async def get_themes(
    language: LanguageParam = None,
    name: str | None = Query(None, max_length=255),
    mine: bool = False,
    verified: bool = True,
    favourites: bool = False,
    order: ThemeOrderBy = ThemeOrderBy.ID,
    descending: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if user is None and (mine or favourites):
        raise AuthError('Authorization required for personal themes')
    query = await get_filtered_themes(user, language, name, mine, verified, favourites)
    query = await apply_themes_ordering(query, order, descending)

    async def add_likes(themes: list[Theme]) -> list[ThemeListItem]:
        likes = await get_likes_counts(db, [theme.id for theme in themes])
        return [ThemeListItem.model_validate(theme, update={'likes': likes.get(theme.id, 0)}) for theme in themes]

    return await paginate(db, query, transformer=add_likes)


@router.get(
    '/{theme_id}',
    response_model=ThemeDetailsResponse,
    responses={404: {'description': 'Theme not found', 'model': ErrorResponse}},
)
async def get_theme(
    theme_id: int, db: AsyncSession = Depends(get_db), user: User | None = Depends(get_optional_user)
) -> ThemeDetailsResponse:
    theme = await get_theme_or_404(db, theme_id, user)
    track('theme_viewed', user_id=user.id if user else None, props={'theme_id': theme.id})
    return ThemeDetailsResponse.model_validate(
        theme,
        update={'likes': len(theme.favourited_by), 'favourite': user is not None and user in theme.favourited_by},
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
        track(
            'theme_created',
            user_id=user.id,
            props={'theme_id': theme_record.id, 'language': theme_record.language, 'public': theme_record.public},
        )
        if theme_record.public:
            track('theme_published', user_id=user.id, props={'theme_id': theme_record.id})
        return theme_record
    except IntegrityError as e:
        logger.error('Could not create new theme: %s', e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f'Theme with name {theme.name} already exists'
        ) from e


@router.put(
    '/{theme_id}',
    response_model=ThemeDetailsResponse,
    responses={
        403: {'description': 'User cannot change specified theme', 'model': ErrorResponse},
        404: {'description': 'Theme not found', 'model': ErrorResponse},
    },
)
async def update_theme(
    theme_id: int,
    theme_info: ThemeUpdatePayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThemeDetailsResponse:
    theme = await get_theme_for_update_or_404(db, theme_id, user)
    theme.description = theme_info.description.model_dump()
    if theme_info.summary is not None:
        theme.summary = theme_info.summary

    db.add(theme)
    await db.commit()
    await db.refresh(theme)

    return ThemeDetailsResponse.model_validate(
        theme, update={'likes': len(theme.favourited_by), 'favourite': user in theme.favourited_by}
    )


@router.patch(
    '/{theme_id}',
    response_model=ThemeDetailsResponse,
    responses={
        403: {'description': 'User cannot change specified theme', 'model': ErrorResponse},
        404: {'description': 'Theme not found', 'model': ErrorResponse},
    },
)
async def change_theme_visibility(
    theme_id: int,
    theme_info: ThemeVisibilityPayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThemeDetailsResponse:
    theme = await get_theme_for_update_or_404(db, theme_id, user)
    became_public = theme_info.public and not theme.public
    theme.public = theme_info.public

    db.add(theme)
    await db.commit()
    await db.refresh(theme)
    if became_public:
        track('theme_published', user_id=user.id, props={'theme_id': theme.id})

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
    track('theme_favourited', user_id=user.id, props={'theme_id': theme.id})

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


@router.put(
    '/{theme_id}/cover-image',
    response_model=ThemeDetailsResponse,
    responses={
        403: {'description': 'User cannot change specified theme', 'model': ErrorResponse},
        404: {'description': 'Theme not found', 'model': ErrorResponse},
        413: {'description': 'Uploaded file is too large', 'model': ErrorResponse},
        422: {'description': 'Not a usable image', 'model': ErrorResponse},
    },
)
async def upload_theme_cover_image(
    theme_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThemeDetailsResponse:
    """Upload a cover: it is cropped to 16:9, resized to 640x360 and stored as WebP of at most 256 KB"""
    theme = await get_theme_for_update_or_404(db, theme_id, user)

    data = await file.read(UPLOAD_MAX_BYTES + 1)
    if len(data) > UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail='Image is too large')

    try:
        content = await asyncio.to_thread(make_cover, data)
    except InvalidImageError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)) from e

    filename = await asyncio.to_thread(save_cover, content)
    old_cover = theme.cover_image
    drop_old = bool(old_cover) and not await is_cover_used_by_other_themes(db, old_cover.id, theme.id)
    try:
        theme.cover_image = CoverImage(
            filename=filename, width=COVER_WIDTH, height=COVER_HEIGHT, size=len(content), uploaded_by=user.id
        )
        db.add(theme)
        if drop_old:
            await db.delete(old_cover)
        await db.commit()
    except Exception:
        await db.rollback()
        await asyncio.to_thread(delete_cover_file, filename)
        raise
    if drop_old:
        await asyncio.to_thread(delete_cover_file, old_cover.filename)

    await db.refresh(theme)
    return ThemeDetailsResponse.model_validate(
        theme, update={'likes': len(theme.favourited_by), 'favourite': user in theme.favourited_by}
    )


@router.delete(
    '/{theme_id}/cover-image',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {'description': 'User cannot change specified theme', 'model': ErrorResponse},
        404: {'description': 'Theme not found', 'model': ErrorResponse},
    },
)
async def delete_theme_cover_image(
    theme_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    theme = await get_theme_for_update_or_404(db, theme_id, user)

    old_cover = theme.cover_image
    if old_cover:
        drop_old = not await is_cover_used_by_other_themes(db, old_cover.id, theme.id)
        theme.cover_image = None
        db.add(theme)
        if drop_old:
            await db.delete(old_cover)
        await db.commit()
        if drop_old:
            await asyncio.to_thread(delete_cover_file, old_cover.filename)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
