from fastapi import APIRouter
from datetime import datetime
from config.settings import settings

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "sap_configured": bool(settings.SAP_BEARER_TOKEN)
        }
    }
