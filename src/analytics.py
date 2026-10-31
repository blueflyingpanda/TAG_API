import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from starlette.background import BackgroundTask
from starlette.responses import Response

from conf import settings
from db import Event, async_session

logger = logging.getLogger('analytics')

MAX_ANON_ID_LENGTH = 64


@dataclass(frozen=True, slots=True)
class ClientInfo:
    anon_id: str | None = None
    platform: str | None = None
    app_version: str | None = None


_NO_CLIENT_INFO = ClientInfo()  # frozen dataclass, safe to share as default
_client_info: ContextVar[ClientInfo] = ContextVar('client_info', default=_NO_CLIENT_INFO)
_events: ContextVar[list[Event] | None] = ContextVar('events', default=None)


def _clean(value: str | None, max_length: int) -> str | None:
    value = (value or '').strip()[:max_length]
    return value or None


def set_client_info(anon_id: str | None, platform: str | None, app_version: str | None) -> None:
    _client_info.set(
        ClientInfo(
            anon_id=_clean(anon_id, MAX_ANON_ID_LENGTH),
            platform=_clean(platform, 16),
            app_version=_clean(app_version, 32),
        )
    )


def begin_request() -> None:
    """Start a per-request event buffer. Call once per request, before the endpoint runs."""
    _events.set([])


async def _flush(events: list[Event]) -> None:
    try:
        async with async_session() as session:
            session.add_all(events)
            await session.commit()
    except Exception:
        logger.exception('Could not store %d events', len(events))


def attach_flush(response: Response) -> None:
    """Store buffered events after the response is sent. Keeps any background task the endpoint set."""
    events = _events.get()
    if not events:
        return
    previous = response.background
    flush = BackgroundTask(_flush, events)
    if previous is None:
        response.background = flush
        return

    async def run_both() -> None:
        await previous()
        await flush()

    response.background = BackgroundTask(run_both)


def track(name: str, user_id: int | None = None, props: dict[str, Any] | None = None) -> None:
    """Queue an analytics event; stored after the response is sent. No-op unless COLLECT_ANALYTICS=1."""
    if not settings.collect_analytics:
        return

    events = _events.get()
    if events is None:
        logger.warning('track(%s) called outside a request, event dropped', name)
        return

    info = _client_info.get()
    events.append(
        Event(
            name=name,
            user_id=user_id,
            anon_id=info.anon_id,
            platform=info.platform,
            app_version=info.app_version,
            props=props or {},
        )
    )
