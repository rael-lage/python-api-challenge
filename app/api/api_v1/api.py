from fastapi import APIRouter

from .endpoints.product import router as product_router
from .endpoints.authenticaion import router as auth_router
from .endpoints.client import router as client_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(client_router)
router.include_router(product_router)
