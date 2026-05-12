from fastapi import APIRouter
from app.api.v1.endpoints import auth,expenses

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(expenses.router)