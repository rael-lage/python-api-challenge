from typing import List, Optional

from pydantic import Schema

from .dbmodel import DateTimeModelMixin, DBModelMixin
from .rwmodel import RWModel


class ProductFilterParams(RWModel):
    title: str = ""
    brand: str = ""
    image: str = ""
    preco: str = ""
    reviewScore: str = ""
    favorited: str = ""


class ProductBase(RWModel):
    title: str
    brand: str
    image: str
    preco: str
    reviewScore: str
    favorited: str


class Product(DateTimeModelMixin, ProductBase):
    slug: str
    favorited: bool
    favorites_count: int = Schema(..., alias="favoritesCount")


class ProductInDB(DBModelMixin, Product):
    pass


class ProductInResponse(RWModel):
    product: Product


class ManyProductsInResponse(RWModel):
    products: List[Product]
    favorites_count: int = Schema(..., alias="favoritesCount")


class ProductInCreate(ProductBase):
    pass


class ProductInUpdate(RWModel):
    title: Optional[str] = None
    brand: Optional[str] = None
    image: Optional[str] = None
    preco: Optional[str] = None
    reviewScore: Optional[str] = None
