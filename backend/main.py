from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
from config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="Expense Processing API", 
    version="2.0.0",
    description="Modular expense processing API with SAP Concur integration"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "message": "Expense Reporting API",
        "version": "2.0.0",
        "status": "ready",
        "docs": "/docs",
        "endpoints": {
            "process_receipt": "POST /api/process-receipt",
            "chat": "POST /api/chat",
            "get_reports": "GET /api/reports",
            "create_report": "POST /api/reports",
            "create_expense_entry": "POST /api/expense-entry",
            "add_expense_to_report": "POST /api/add-expense-to-report",
            "health": "GET /api/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)