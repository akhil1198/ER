# concur_test_api.py - SAP Concur Testing FastAPI
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="SAP Concur Testing API", 
    version="1.0.0",
    description="Easy-to-use API for testing SAP Concur integration"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - Update these with your actual values
CONCUR_CONFIG = {
    "base_url": os.getenv("BASE_URL"),
    "client_id": os.getenv("CLIENT_ID"),
    "client_secret": os.getenv("CLIENT_SECRET"),
    "company_uuid": os.getenv("COMPANY_UUID"),
    "access_token": os.getenv("ACCESS_TOKEN"),
    "refresh_token": os.getenv("REFRESH_TOKEN")
}

# Data Models
class ExpenseReportCreate(BaseModel):
    name: str = "API Test Report"
    purpose: str = "Testing SAP Concur API"
    comment: Optional[str] = "Created via FastAPI test endpoint"

class ExpenseEntryCreate(BaseModel):
    report_id: str
    expense_type: str = "MEALS"  # MEALS, AIRFR, LODNG, etc.
    transaction_date: str = "2024-06-27"
    amount: float = 50.00
    currency: str = "USD"
    vendor: str = "Test Vendor"
    city: str = "New York"
    country: str = "US"
    payment_type: str = "CCARD"  # CCARD, CASH, CHECK
    comment: Optional[str] = "Test expense entry"

class TokenRefresh(BaseModel):
    refresh_token: Optional[str] = None

# Helper function to make API calls
async def make_concur_api_call(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make authenticated API call to SAP Concur"""
    url = f"{CONCUR_CONFIG['base_url']}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {CONCUR_CONFIG['access_token']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Print debug info
        print(f"🔗 {method} {url}")
        print(f"📊 Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"❌ Error: {response.text}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if 'response' in locals() else 500,
            detail=f"Concur API error: {str(e)}"
        )

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/auth/refresh-token")
async def refresh_access_token(token_data: TokenRefresh):
    """Refresh the access token"""
    refresh_token = token_data.refresh_token or CONCUR_CONFIG["refresh_token"]
    
    url = f"{CONCUR_CONFIG['base_url']}/oauth2/v0/token"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "client_id": CONCUR_CONFIG["client_id"],
        "client_secret": CONCUR_CONFIG["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        token_response = response.json()
        
        # Update stored token
        CONCUR_CONFIG["access_token"] = token_response["access_token"]
        if "refresh_token" in token_response:
            CONCUR_CONFIG["refresh_token"] = token_response["refresh_token"]
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "expires_in": token_response.get("expires_in"),
            "new_access_token": token_response["access_token"][:50] + "..."
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")

@app.get("/auth/status")
async def get_auth_status():
    """Get current authentication status"""
    return {
        "base_url": CONCUR_CONFIG["base_url"],
        "client_id": CONCUR_CONFIG["client_id"],
        "has_access_token": bool(CONCUR_CONFIG["access_token"]),
        "has_refresh_token": bool(CONCUR_CONFIG["refresh_token"]),
        "token_preview": CONCUR_CONFIG["access_token"][:50] + "..." if CONCUR_CONFIG["access_token"] else None
    }

# =============================================================================
# USER & CONFIGURATION ENDPOINTS
# =============================================================================

@app.get("/user/profile")
def get_user_profile():
    """Get current user profile"""
    headers = {
        "Authorization": f"Bearer {CONCUR_CONFIG['access_token']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get("https://us2.api.concursolutions.com/profile/identity/v4.1/Users", headers=headers)
    return {
        "success": True,
        "data": response.json()
    }


@app.get("/config/expense-types")
async def get_expense_types():
    """Get available expense types"""
    result = await make_concur_api_call("GET", "/api/v3.0/expense/expensegroupconfigurations")
    return {
        "success": True,
        "data": result,
        "summary": "Available expense types for creating expenses"
    }

@app.get("/config/countries")
async def get_countries():
    """Get available countries"""
    result = await make_concur_api_call("GET", "/api/v3.0/common/countries")
    return {
        "success": True,
        "data": result
    }

@app.get("/config/currencies")
async def get_currencies():
    """Get available currencies"""
    result = await make_concur_api_call("GET", "/api/v3.0/common/currencies")
    return {
        "success": True,
        "data": result
    }

# =============================================================================
# EXPENSE REPORT ENDPOINTS
# =============================================================================

## fetches expense reports based on report ID, refresh bearer token when trying. 
# curl --location --request GET 'https://www-us2.api.concursolutions.com/expensereports/v4/users/9e4f220f-b716-4738-9105-1153e04188ae/context/TRAVELER/reports/341AD93E74CB4776942B/expenses' \
# --header 'Authorization: Bearer eyJraWQiOiIxNDU1NjE0MDIyIiwiYWxnIjoiUlMyNTYiLCJ0eXAiOiJKV1QifQ.eyJjb25jdXIuc2NvcGVzIjpbIm9wZW5pZCIsInF1aWNrZXhwZW5zZS53cml0ZW9ubHkiLCJ1c2VyLnJlYWQiLCJyZWNlaXB0cy53cml0ZW9ubHkiLCJleHBlbnNlLnJlcG9ydC5yZWFkIiwiZXhwZW5zZS5yZXBvcnQucmVhZHdyaXRlIiwiZXhwZW5zZS5yZXBvcnQud29ya2Zsb3dzdGF0dXMud3JpdGUiXSwiYXVkIjoiKiIsImNvbmN1ci5hcHBJZCI6IjlhMGE2N2NkLTU0YmMtNGZlNi1hODhmLWVkNmU1MjcwNDNjOSIsInN1YiI6ImQ5ODc2OWQwLTIyZTAtNDQ4NS1hMTZkLTI5NzczMTRiZjM5NCIsImlzcyI6Imh0dHBzOi8vdXMyLmFwaS5jb25jdXJzb2x1dGlvbnMuY29tIiwiY29uY3VyLnByb2ZpbGUiOiJodHRwczovL3VzMi5hcGkuY29uY3Vyc29sdXRpb25zLmNvbS9wcm9maWxlL3YxL3ByaW5jaXBhbHMvZDk4NzY5ZDAtMjJlMC00NDg1LWExNmQtMjk3NzMxNGJmMzk0IiwiZXhwIjoxNzUxNDA0ODIxLCJjb25jdXIudmVyc2lvbiI6MywiY29uY3VyLnR5cGUiOiJjb21wYW55IiwiY29uY3VyLmFwcCI6Imh0dHBzOi8vdXMyLmFwaS5jb25jdXJzb2x1dGlvbnMuY29tL3Byb2ZpbGUvdjEvYXBwcy85YTBhNjdjZC01NGJjLTRmZTYtYTg4Zi1lZDZlNTI3MDQzYzkiLCJuYmYiOjE3NTE0MDEyMTEsImlhdCI6MTc1MTQwMTIyMX0.dlGrmHlCJXwGkQJIkZMLtb62vUfzXcErClEUaZJ4AO6eF4lKlhMLofQbFIexe93ZXiDw4Rd68m3dV0HMARMuz5bx94HGeYLCz52vrcbP02fY10Z5sssertc07wBUQQNuQS662c4YkmpBKiMt4coGOMDFEhqjArGmnY5JyJfP3VazxTMuN3Gv7WK2IwFX_LF_94nAWNmPH_pJLrYhVMbg98BmJbnhQsc84faMbczPQNWE2ryvUOG_aSHP7yLDaxcZeYItB5SwTuTEO-85V1pTbNwgUHyJsXpMXv66UV5eOHQf80IuA0nrtaWYCUdUrWBamCy2XT0aENyZ_AZ75l5OBg' \
# --header 'Content-Type: application/json'

@app.get("/reports")
async def list_expense_reports():
    """List all expense reports"""
    result = await make_concur_api_call("GET", "/api/v3.0/expense/reports")
    return {
        "success": True,
        "data": result,
        "summary": f"Found {len(result.get('Items', []))} expense reports"
    }

@app.post("/reports/create")
async def create_expense_report(report_data: ExpenseReportCreate):
    """Create a new expense report"""
    concur_data = {
        "Name": report_data.name,
        "Purpose": report_data.purpose,
        "Comment": report_data.comment
    }
    
    result = await make_concur_api_call("POST", "/api/v3.0/expense/reports", concur_data)
    
    return {
        "success": True,
        "message": "Expense report created successfully",
        "report_id": result.get("ID"),
        "data": result
    }

@app.get("/reports/{report_id}")
async def get_expense_report(report_id: str):
    """Get details of a specific expense report"""
    result = await make_concur_api_call("GET", f"/api/v3.0/expense/reports/{report_id}")
    return {
        "success": True,
        "data": result
    }

@app.post("/reports/{report_id}/submit")
async def submit_expense_report(report_id: str, comment: Optional[str] = "Submitted via API"):
    """Submit expense report for approval"""
    submit_data = {"comment": comment}
    
    result = await make_concur_api_call("POST", f"/api/v3.0/expense/reports/{report_id}/submit", submit_data)
    
    return {
        "success": True,
        "message": f"Report {report_id} submitted for approval",
        "data": result
    }

# =============================================================================
# EXPENSE ENTRY ENDPOINTS
# =============================================================================

@app.get("/reports/{report_id}/entries")
async def list_expense_entries(report_id: str):
    """List entries for a specific report"""
    result = await make_concur_api_call("GET", f"/api/v3.0/expense/entries?reportID={report_id}")
    return {
        "success": True,
        "data": result,
        "summary": f"Found {len(result.get('Items', []))} expense entries"
    }

@app.post("/entries/create")
async def create_expense_entry(entry_data: ExpenseEntryCreate):
    """Create a new expense entry"""
    concur_data = {
        "ReportID": entry_data.report_id,
        "ExpenseTypeCode": entry_data.expense_type,
        "TransactionDate": entry_data.transaction_date,
        "TransactionAmount": entry_data.amount,
        "TransactionCurrencyCode": entry_data.currency,
        "VendorDescription": entry_data.vendor,
        "City": entry_data.city,
        "CountryCode": entry_data.country,
        "PaymentTypeCode": entry_data.payment_type,
        "Comment": entry_data.comment
    }
    
    result = await make_concur_api_call("POST", "/api/v3.0/expense/entries", concur_data)
    
    return {
        "success": True,
        "message": "Expense entry created successfully",
        "entry_id": result.get("ID"),
        "data": result
    }

@app.get("/entries/{entry_id}")
async def get_expense_entry(entry_id: str):
    """Get details of a specific expense entry"""
    result = await make_concur_api_call("GET", f"/api/v3.0/expense/entries/{entry_id}")
    return {
        "success": True,
        "data": result
    }

@app.put("/entries/{entry_id}")
async def update_expense_entry(entry_id: str, amount: Optional[float] = None, comment: Optional[str] = None):
    """Update an expense entry"""
    update_data = {}
    if amount is not None:
        update_data["TransactionAmount"] = amount
    if comment is not None:
        update_data["Comment"] = comment
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await make_concur_api_call("PUT", f"/api/v3.0/expense/entries/{entry_id}", update_data)
    
    return {
        "success": True,
        "message": f"Entry {entry_id} updated successfully",
        "data": result
    }

@app.delete("/entries/{entry_id}")
async def delete_expense_entry(entry_id: str):
    """Delete an expense entry"""
    result = await make_concur_api_call("DELETE", f"/api/v3.0/expense/entries/{entry_id}")
    
    return {
        "success": True,
        "message": f"Entry {entry_id} deleted successfully",
        "data": result
    }

# =============================================================================
# QUICK TEST ENDPOINTS
# =============================================================================

@app.post("/test/create-sample-report")
async def create_sample_expense_report():
    """Create a complete sample expense report with entries"""
    
    # Step 1: Create report
    report_data = {
        "Name": f"Sample Report {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "Purpose": "Complete API testing with sample data",
        "Comment": "Auto-generated sample report for testing"
    }
    
    report_result = await make_concur_api_call("POST", "/api/v3.0/expense/reports", report_data)
    report_id = report_result.get("ID")
    
    if not report_id:
        raise HTTPException(status_code=500, detail="Failed to create report")
    
    # Step 2: Add sample entries
    sample_entries = [
        {
            "ReportID": report_id,
            "ExpenseTypeCode": "MEALS",
            "TransactionDate": "2024-06-27",
            "TransactionAmount": 45.67,
            "TransactionCurrencyCode": "USD",
            "VendorDescription": "Restaurant ABC",
            "City": "New York",
            "CountryCode": "US",
            "PaymentTypeCode": "CCARD",
            "Comment": "Business lunch with client"
        },
        {
            "ReportID": report_id,
            "ExpenseTypeCode": "AIRFR",
            "TransactionDate": "2024-06-27",
            "TransactionAmount": 350.00,
            "TransactionCurrencyCode": "USD",
            "VendorDescription": "Airline XYZ",
            "City": "Chicago",
            "CountryCode": "US",
            "PaymentTypeCode": "CCARD",
            "Comment": "Flight for business meeting"
        },
        {
            "ReportID": report_id,
            "ExpenseTypeCode": "LODNG",
            "TransactionDate": "2024-06-27",
            "TransactionAmount": 150.00,
            "TransactionCurrencyCode": "USD",
            "VendorDescription": "Hotel ABC",
            "City": "Chicago",
            "CountryCode": "US",
            "PaymentTypeCode": "CCARD",
            "Comment": "Overnight stay for business meeting"
        }
    ]
    
    created_entries = []
    for entry_data in sample_entries:
        try:
            entry_result = await make_concur_api_call("POST", "/api/v3.0/expense/entries", entry_data)
            created_entries.append(entry_result)
        except Exception as e:
            print(f"Failed to create entry: {e}")
    
    return {
        "success": True,
        "message": "Sample expense report created with entries",
        "report_id": report_id,
        "report_details": report_result,
        "entries_created": len(created_entries),
        "entries": created_entries,
        "next_steps": [
            f"View report: GET /reports/{report_id}",
            f"Submit report: POST /reports/{report_id}/submit",
            "Check SAP Concur web interface to see the report"
        ]
    }

@app.get("/test/workflow")
async def get_test_workflow():
    """Get a suggested testing workflow"""
    return {
        "testing_workflow": [
            "1. Check authentication: GET /auth/status",
            "2. Get user profile: GET /user/profile", 
            "3. View expense types: GET /config/expense-types",
            "4. Create sample report: POST /test/create-sample-report",
            "5. List all reports: GET /reports",
            "6. Submit report for approval: POST /reports/{report_id}/submit",
            "7. Check SAP Concur web interface to verify"
        ],
        "available_endpoints": {
            "auth": ["/auth/status", "/auth/refresh-token"],
            "config": ["/config/expense-types", "/config/countries", "/config/currencies"],
            "reports": ["/reports", "/reports/create", "/reports/{id}", "/reports/{id}/submit"],
            "entries": ["/entries/create", "/entries/{id}", "/reports/{id}/entries"],
            "testing": ["/test/create-sample-report", "/test/workflow"]
        }
    }

@app.get("/")
async def root():
    """API information and quick start guide"""
    return {
        "title": "SAP Concur Testing API",
        "version": "1.0.0",
        "description": "Easy-to-use FastAPI for testing SAP Concur integration",
        "authentication_status": bool(CONCUR_CONFIG["access_token"]),
        "quick_start": [
            "1. Check authentication: GET /auth/status",
            "2. Test user profile: GET /user/profile",
            "3. Create sample report: POST /test/create-sample-report",
            "4. View interactive docs: /docs"
        ],
        "documentation": "/docs",
        "base_url": CONCUR_CONFIG["base_url"]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SAP Concur Testing API...")
    print("📖 View interactive docs at: http://localhost:8000/docs")
    print("🧪 Quick test: http://localhost:8000/test/workflow")
    uvicorn.run(app, host="0.0.0.0", port=8000)