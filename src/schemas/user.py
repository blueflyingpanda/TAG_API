from sqlmodel import SQLModel


class UserBase(SQLModel):
    email: str
    picture: str = ''
    admin: bool = False
