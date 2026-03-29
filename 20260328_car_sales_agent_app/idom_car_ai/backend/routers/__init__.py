"""API routers package."""

from idom_car_ai.backend.routers.customers import router as customers_router
from idom_car_ai.backend.routers.recommendations import router as recommendations_router
from idom_car_ai.backend.routers.chat import router as chat_router
from idom_car_ai.backend.routers.admin import router as admin_router

__all__ = [
    "customers_router",
    "recommendations_router",
    "chat_router",
    "admin_router",
]
