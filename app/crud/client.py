from asyncpg import Connection
from pydantic import EmailStr

from app.models.client import ClientInCreate, ClientInDB, ClientInUpdate


async def get_client(conn: Connection, name: str) -> ClientInDB:
    row = await conn.fetchrow(
        """
        SELECT id, name, email, hashed_password, created_at, updated_at
        FROM clients
        WHERE name = $1
        """,
        name,
    )
    if row:
        return ClientInDB(**row)


async def get_client_by_email(conn: Connection, email: EmailStr) -> ClientInDB:
    row = await conn.fetchrow(
        """
        SELECT id, name, email, hashed_password, created_at, updated_at
        FROM clients
        WHERE email = $1
        """,
        email,
    )
    if row:
        return ClientInDB(**row)


async def create_client(conn: Connection, client: ClientInCreate) -> ClientInDB:
    dbclient = ClientInDB(**client.dict())
    dbclient.change_password(client.password)

    row = await conn.fetchrow(
        """
        INSERT INTO clients (name, email, hashed_password) 
        VALUES ($1, $2, $3, $4)
        RETURNING id, created_at, updated_at
        """,
        dbclient.name,
        dbclient.email,
        dbclient.hashed_password,
    )

    dbclient.id = row["id"]
    dbclient.created_at = row["created_at"]
    dbclient.updated_at = row["updated_at"]

    return dbclient


async def update_client(conn: Connection, email: str, client: ClientInUpdate) -> ClientInDB:
    dbclient = await get_client_by_email(conn, email)

    dbclient.name = client.name or dbclient.name
    dbclient.email = client.email or dbclient.email
    if client.password:
        dbclient.change_password(client.password)

    updated_at = await conn.fetchval(
        """
        UPDATE clients
        SET name = $1, email = $2, hashed_password = $3
        WHERE name = $4
        RETURNING updated_at
        """,
        dbclient.name,
        dbclient.email,
        dbclient.hashed_password,
        name,
    )

    dbclient.updated_at = updated_at
    return dbclient
