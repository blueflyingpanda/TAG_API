from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette import status
from starlette.responses import Response

from analytics import track
from db import User
from utils.oauth import get_optional_user

router = APIRouter(prefix='/events', tags=['Events'])


class ClientEventPayload(BaseModel):
    # Only events the server cannot observe by itself
    name: Literal['theme_shared']
    props: dict[str, Any] = Field(default_factory=dict, max_length=10)


@router.post('/', status_code=status.HTTP_204_NO_CONTENT)
async def post_event(event: ClientEventPayload, user: User | None = Depends(get_optional_user)):
    """Record a client-side analytics event. Accepted and ignored when analytics collection is off."""
    track(event.name, user_id=user.id if user else None, props=event.props)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
