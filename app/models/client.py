from typing import Optional

from pydantic import EmailStr, UrlStr

from app.core.security import generate_salt, get_password_hash, verify_password

from .dbmodel import DBModelMixin
from .rwmodel import RWModel


class ClientBase(RWModel):
    name: str
    email: EmailStr


class ClientInDB(DBModelMixin, ClientBase):
    salt: str = ""
    hashed_password: str = ""

    def check_password(self, password: str):
        return verify_password(self.salt + password, self.hashed_password)

    def change_password(self, password: str):
        self.salt = generate_salt()
        self.hashed_password = get_password_hash(self.salt + password)


class Client(ClientBase):
    token: str


class ClientInResponse(RWModel):
    client: Client


class ClientInLogin(RWModel):
    email: EmailStr
    password: str


class ClientInCreate(ClientInLogin):
    name: str


class ClientInUpdate(RWModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
