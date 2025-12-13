from datetime import datetime

from sqlmodel import SQLModel


class UserRead(SQLModel):
    id: int
    email: str
    picture: str
    admin: bool
    created_at: datetime
    last_login: datetime | None
