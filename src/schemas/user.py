from sqlmodel import SQLModel


class UserBase(SQLModel):
    user_id: int
    email: str | None = None
    username: str | None = None
    picture: str = ''
    admin: bool = False
