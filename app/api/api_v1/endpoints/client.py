from fastapi import APIRouter, Body, Depends

from app.core.jwt import get_current_client_authorizer
from app.crud.shortcuts import check_free_email
from app.crud.client import update_client
from app.db.database import DataBase, get_database
from app.models.client import Client, ClientInResponse, ClientInUpdate

router = APIRouter()


@router.get("/client", response_model=ClientInResponse, tags=["clients"])
async def retrieve_current_client(client: Client = Depends(get_current_client_authorizer())):
    return ClientInResponse(client=client)


@router.put("/client", response_model=ClientInResponse, tags=["clients"])
async def update_current_client(
    client: ClientInUpdate = Body(..., embed=True),
    current_client: Client = Depends(get_current_client_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        if client.email == current_client.email:
            client.email = None

        await check_free_email(conn, client.email)

        async with conn.transaction():
            dbclient = await update_client(conn, current_client.email, client)
            return ClientInResponse(client=Client(**dbclient.dict(), token=current_client.token))
