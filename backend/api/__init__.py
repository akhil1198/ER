from fastapi import APIRouter
from .routes import chat, expense, reports, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router)
api_router.include_router(expense.router)
api_router.include_router(reports.router)
api_router.include_router(health.router)
