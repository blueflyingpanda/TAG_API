from html import escape

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from conf import settings
from dal import get_theme_details
from db import get_db

router = APIRouter(prefix='/share', tags=['Share'], include_in_schema=False)

DEFAULT_DESCRIPTION = 'T.A.G. — Themed Alias Game. Pick a theme, split into teams and guess the words.'


def render_share_page(theme_id: int, name: str | None, summary: str | None, image_url: str | None, fe_url: str) -> str:
    base = fe_url.rstrip('/')
    target = f'{base}/theme/{theme_id}/'
    title = escape(name or 'T.A.G.')
    description = escape(summary or DEFAULT_DESCRIPTION)
    image = escape(image_url or f'{base}/tag.jpeg')
    url = escape(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} · T.A.G.</title>
<meta name="description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="T.A.G.">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">
<meta http-equiv="refresh" content="0; url={url}">
<link rel="canonical" href="{url}">
</head>
<body>
<script>location.replace({target!r});</script>
<p><a href="{url}">{title}</a></p>
</body>
</html>
"""


@router.get('/themes/{theme_id}', response_class=HTMLResponse)
@router.get('/themes/{theme_id}/', response_class=HTMLResponse)
async def share_theme(theme_id: int, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    """Link-preview page for shared themes: Open Graph tags for crawlers, instant redirect to the web app for people.

    Only public themes are described; anything else gets the generic card.
    """
    theme = await get_theme_details(db, None, theme_id)
    page = render_share_page(
        theme_id,
        theme.name if theme else None,
        theme.summary if theme else None,
        theme.cover_image_url if theme else None,
        settings.fe_url,
    )
    return HTMLResponse(page, headers={'Cache-Control': 'public, max-age=300'})
