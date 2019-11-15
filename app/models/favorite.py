from typing import List, Optional

from pydantic import Schema

from .dbmodel import DateTimeModelMixin, DBModelMixin
from .client import Client
from .product import Product
from .rwmodel import RWModel


class FavoriteFilterParams(RWModel):
    client: str = ""
    product: str = ""

class FavoriteBase(RWModel):
    pass

class Favorite(DateTimeModelMixin, FavoriteBase):
    client: Client
    product: Product

class FavoriteInDB(DBModelMixin, Favorite):
    pass


class FavoriteInResponse(RWModel):
    favorite: Favorite


class ManyFavoritesInResponse(RWModel):
    favorites: List[Favorite]

class FavoriteInCreate(FavoriteBase):
    pass
