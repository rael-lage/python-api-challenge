from datetime import timedelta

from fastapi import APIRouter, Body, Depends
from starlette.exceptions import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.jwt import create_access_token
from app.crud.shortcuts import check_free_email
from app.crud.client import create_client, get_client_by_email
from app.db.database import DataBase, get_database
from app.models.client import Client, ClientInCreate, ClientInLogin, ClientInResponse

router = APIRouter()


@router.post("/clients/login", response_model=ClientInResponse, tags=["authentication"])
async def login(
    client: ClientInLogin = Body(..., embed=True), db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        dbclient = await get_client_by_email(conn, client.email)
        if not dbclient or not dbclient.check_password(client.password):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Incorrect email or password"
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"email": dbclient.email}, expires_delta=access_token_expires
        )
        return ClientInResponse(client=Client(**dbclient.dict(), token=token))


@router.post(
    "/clients",
    response_model=ClientInResponse,
    tags=["authentication"],
    status_code=HTTP_201_CREATED,
)
async def register(
    client: ClientInCreate = Body(..., embed=True), db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        await check_free_email(conn, client.email)

        async with conn.transaction():
            dbclient = await create_client(conn, client)
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = create_access_token(
                data={"email": dbclient.email}, expires_delta=access_token_expires
            )

            return ClientInResponse(client=Client(**dbclient.dict(), token=token))
