from typing import Optional

from asyncpg import Connection
from pydantic import EmailStr
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.models.product import ProductInDB

from .product import get_product_by_slug
from .client import get_client, get_client_by_email


async def check_free_email(
    conn: Connection, email: Optional[EmailStr] = None
):
    if email:
        user_by_email = await get_user_by_email(conn, email)
        if user_by_email:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Client with this email already exists",
            )


async def get_product_or_404(
    conn: Connection, slug: str, email: Optional[str] = None
) -> ProductInDB:
    searched_product = await get_product_by_slug(conn, slug, email)
    if not searched_product:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found",
        )
    return searched_product
