from fastapi import APIRouter

from src.api.routes.tickets import router as tickets_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(tickets_router)
