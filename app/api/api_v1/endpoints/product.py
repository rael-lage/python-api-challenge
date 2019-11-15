from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from slugify import slugify
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.core.jwt import get_current_client_authorizer
from app.core.utils import create_aliased_response
from app.crud.product import (
    add_product_to_favorites,
    create_product_by_slug,
    delete_product_by_slug,
    get_product_by_slug,
    remove_product_from_favorites,
    update_product_by_slug,
)
from app.crud.shortcuts import (
    get_product_or_404,
)
from app.db.database import DataBase, get_database
from app.models.product import (
    ProductInCreate,
    ProductInResponse,
    ProductInUpdate,
    ManyProductsInResponse,
)
from app.models.client import Client

router = APIRouter()


@router.get("/products", response_model=ManyProductsInResponse, tags=["products"])
async def get_products(
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbproducts = await get_products(
            conn
        )
        if not dbproducts:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Products not found",
            )

        return create_aliased_response(
            ManyProductsInResponse(products=dbproducts, products_count=len(dbproducts))
        )

@router.get("/products/{slug}", response_model=ProductInResponse, tags=["products"])
async def get_product(
    slug: str = Path(..., min_length=1),
    client: Optional[Client] = Depends(get_current_client_authorizer(required=False)),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbproduct = await get_product_by_slug(
            conn, slug
        )
        if not dbproduct:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Product with slug '{slug}' not found",
            )

        return create_aliased_response(ProductInResponse(product=dbproduct))


@router.post(
    "/products",
    response_model=ProductInResponse,
    tags=["products"],
    status_code=HTTP_201_CREATED,
)
async def create_new_product(
    product: ProductInCreate = Body(..., embed=True),
    client: Client = Depends(get_current_client_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        product_by_slug = await get_product_by_slug(
            conn, slugify(product.title)
        )
        if product_by_slug:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Product with slug '{product_by_slug.slug}' already exists",
            )

        async with conn.transaction():
            dbproduct = await create_product_by_slug(conn, product)
            return create_aliased_response(ProductInResponse(product=dbproduct))


@router.put("/products/{slug}", response_model=ProductInResponse, tags=["products"])
async def update_product(
    slug: str = Path(..., min_length=1),
    product: ProductInUpdate = Body(..., embed=True),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            dbproduct = await update_product_by_slug(conn, slug, product)
            return create_aliased_response(ProductInResponse(product=dbproduct))


@router.delete("/products/{slug}", tags=["products"], status_code=HTTP_204_NO_CONTENT)
async def delete_product(
    slug: str = Path(..., min_length=1),
    client: Client = Depends(get_current_client_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await delete_product_by_slug(conn, slug, client.clientname)


@router.post(
    "/products/{slug}/favorite", response_model=ProductInResponse, tags=["products"]
)
async def favorite_product(
    slug: str = Path(..., min_length=1),
    client: Client = Depends(get_current_client_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbproduct = await get_product_or_404(conn, slug)
        if dbproduct.favorited:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="You already added this product to favorites",
            )

        dbproduct.favorited = True
        dbproduct.favorites_count += 1

        async with conn.transaction():
            await add_product_to_favorites(conn, slug, client.email)
            return create_aliased_response(ProductInResponse(product=dbproduct))


@router.delete(
    "/products/{slug}/favorite", response_model=ProductInResponse, tags=["products"]
)
async def delete_product_from_favorites(
    slug: str = Path(..., min_length=1),
    client: Client = Depends(get_current_client_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbproduct = await get_product_or_404(conn, slug, client.email)

        if not dbproduct.favorited:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="You don't have this product in favorites",
            )

        dbproduct.favorited = False
        dbproduct.favorites_count -= 1

        async with conn.transaction():
            await remove_product_from_favorites(conn, slug, client.email)
            return create_aliased_response(ProductInResponse(product=dbproduct))
