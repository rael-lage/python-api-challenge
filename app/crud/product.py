from typing import List, Optional

from asyncpg import Connection
from slugify import slugify

from app.models.product import (
    ProductFilterParams,
    ProductInCreate,
    ProductInDB,
    ProductInUpdate,
)

from .client import get_client_by_email


async def is_product_favorited_by_client(
    conn: Connection, slug: str, email: str
) -> bool:
    return await conn.fetchval(
        """
        SELECT CASE WHEN client_id IS NULL THEN FALSE ELSE TRUE END AS favorited
        FROM favorites
        WHERE 
            client_id = (SELECT id FROM clients WHERE email = $1) 
            AND
            product_id = (SELECT id FROM products WHERE slug = $2)
        """,
        email,
        slug,
    )


async def add_product_to_favorites(conn: Connection, slug: str, email: str):
    await conn.execute(
        """
        INSERT INTO favorites (client_id, product_id) 
        VALUES (
            (SELECT id FROM clients WHERE email = $2),
            (SELECT id FROM products WHERE slug = $1) 
        )
        """,
        slug,
        email,
    )


async def remove_product_from_favorites(conn: Connection, slug: str, email: str):
    await conn.execute(
        """
        DELETE FROM favorites
        WHERE 
            product_id = (SELECT id FROM products WHERE slug = $1) 
            AND 
            client_id = (SELECT id FROM clients WHERE email = $2)
        """,
        slug,
        email,
    )


async def get_favorites_count_for_product(conn: Connection, slug: str):
    return await conn.fetchval(
        """
        SELECT count(*) as favorites_count
        FROM favorites
        WHERE product_id = (SELECT id FROM products WHERE slug = $1)
        """,
        slug,
    )

async def get_products(
    conn: Connection
) -> ProductInDB:
    product_info_row = await conn.fetchrow(
        """
        SELECT id, slug, title, brand, image, preco, reviewScore, created_at, updated_at
        FROM products
        """,
    )
    if product_info_row:
        favorites_count = await get_favorites_count_for_product(conn)

        return ProductInDB(
            **product_info_row,
            favorites_count=favorites_count,
        )


async def get_product_by_slug(
    conn: Connection, slug: str
) -> ProductInDB:
    product_info_row = await conn.fetchrow(
        """
        SELECT id, slug, title, brand, image, preco, reviewScore, created_at, updated_at
        FROM products
        WHERE slug = $1
        """,
        slug,
    )
    if product_info_row:
        favorites_count = await get_favorites_count_for_product(conn, slug)
        favorited_by_client = await is_product_favorited_by_client(conn, slug, email)

        return ProductInDB(
            **product_info_row,
            client=client,
            favorited=favorited_by_client,
            favorites_count=favorites_count,
        )


async def create_product_by_slug(
    conn: Connection, product: ProductInCreate, email: str
) -> ProductInDB:
    slug = slugify(product.title)

    row = await conn.fetchrow(
        """
        INSERT INTO products (slug, title, brand, image, preco, reviewScore) 
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING 
            id, 
            title,
            brand,
            image,
            preco,
            reviewScore,
            created_at, 
            updated_at
        """,
        slug,
        product.title,
        product.brand,
        product.image,
        product.preco,
        product.reviewScore,
    )

    client = await get_client_by_email(conn, row["client_email"], "")

    return ProductInDB(
        **row,
        client=client,
        favorites_count=1,
        favorited=True,
    )


async def update_product_by_slug(
    conn: Connection, slug: str, product: ProductInUpdate, email: str
) -> ProductInDB:
    dbproduct = await get_product_by_slug(conn, slug)

    if product.title:
        dbproduct.slug = slugify(product.title)
        dbproduct.title = product.title
        dbproduct.brand = product.brand
        dbproduct.image = product.image
        dbproduct.preco = product.preco
        dbproduct.reviewScore = product.reviewScore
        

    row = await conn.fetchrow(
        """
        UPDATE products
        SET slug = $1, title = $2, brand = $3, image = $4, preco = $5, reviewScore = $6
        WHERE slug = $7
        RETURNING updated_at
        """,
        dbproduct.slug,
        dbproduct.title,
        dbproduct.brand,
        dbproduct.image,
        dbproduct.preco,
        dbproduct.reviewScore,
        slug,
    )

    dbproduct.updated_at = row["updated_at"]
    return dbproduct


async def delete_product_by_slug(conn: Connection, slug: str, email: str):
    await conn.execute(
        """
        DELETE FROM products 
        WHERE slug = $1
        """,
        slug,
    )