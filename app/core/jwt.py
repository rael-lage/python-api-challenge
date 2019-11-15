from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, Header
from jwt import PyJWTError
from starlette.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.crud.client import get_client_by_email
from app.db.database import DataBase, get_database
from app.models.token import TokenPayload
from app.models.client import Client

from .config import JWT_TOKEN_PREFIX, SECRET_KEY

ALGORITHM = "HS256"
access_token_jwt_subject = "access"


def _get_authorization_token(authorization: str = Header(...)):
    token_prefix, token = authorization.split(" ")
    if token_prefix != JWT_TOKEN_PREFIX:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid authorization type"
        )

    return token


async def _get_current_client(
    db: DataBase = Depends(get_database), token: str = Depends(_get_authorization_token)
) -> Client:
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

    async with db.pool.acquire() as conn:
        dbclient = await get_client_by_email(conn, token_data.email)
        if not dbclient:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Client not found")

        client = Client(**dbclient.dict(), token=token)
        return client


def _get_authorization_token_optional(authorization: str = Header(None)):
    if authorization:
        return _get_authorization_token(authorization)
    return ""


async def _get_current_client_optional(
    db: DataBase = Depends(get_database),
    token: str = Depends(_get_authorization_token_optional),
) -> Optional[Client]:
    if token:
        return await _get_current_client(db, token)

    return None


def get_current_client_authorizer(*, required: bool = True):
    if required:
        return _get_current_client
    else:
        return _get_current_client_optional


def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "sub": access_token_jwt_subject})
    encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)
    return encoded_jwt
