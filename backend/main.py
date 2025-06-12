# main.py - FastAPI Backend MVP with SSL Fix
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import openai
import base64
import json
import os
import ssl
import certifi
import httpx
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Expense Reporting MVP", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Both Vite and CRA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response model for extracted expense data
class ExpenseData(BaseModel):
    expense_type: Optional[str] = None
    transaction_date: Optional[str] = None
    business_purpose: Optional[str] = None
    travel_type: Optional[str] = None
    meal_type: Optional[str] = None
    vendor: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    payment_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    allocate_to_another_business_unit: Optional[bool] = False
    business_unit: Optional[str] = None
    comment: Optional[str] = None

class ExpenseResponse(BaseModel):
    success: bool
    expense_data: Optional[ExpenseData] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

# ChatGPT prompt for expense data extraction
EXPENSE_EXTRACTION_PROMPT = """
You are an expert at extracting expense information from receipt images. 
Analyze the receipt image and extract the following information in JSON format:

Required fields:
- expense_type: Categorize as one of: "Meals", "Travel", "Accommodation", "Transportation", "Office Supplies", "Software", "Other"
- transaction_date: Date in YYYY-MM-DD format
- business_purpose: Infer likely business purpose based on vendor/items
- travel_type: If travel-related, specify "Domestic" or "International", otherwise null
- meal_type: If meal, specify "Breakfast", "Lunch", "Dinner", "Snack", otherwise null
- vendor: Business/vendor name
- city: City where transaction occurred
- country: Country where transaction occurred
- payment_type: "Credit Card", "Cash", "Bank Transfer", or "Other"
- amount: Total amount as number
- currency: Currency code (USD, EUR, etc.)
- allocate_to_another_business_unit: false (default)
- business_unit: null (default)
- comment: Any additional notes or itemized details

Return ONLY valid JSON format with these exact field names. If information is not available, use null for strings, 0 for amounts, and false for booleans.

Example response:
{
  "expense_type": "Meals",
  "transaction_date": "2024-01-15",
  "business_purpose": "Client lunch meeting",
  "travel_type": null,
  "meal_type": "Lunch",
  "vendor": "Restaurant ABC",
  "city": "New York",
  "country": "USA",
  "payment_type": "Credit Card",
  "amount": 45.67,
  "currency": "USD",
  "allocate_to_another_business_unit": false,
  "business_unit": null,
  "comment": "Lunch with client to discuss project requirements"
}
"""

# Create SSL context for HTTPS requests
def create_ssl_context():
    """Create SSL context with proper certificate validation"""
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        return ssl_context
    except Exception as e:
        print(f"SSL context creation failed: {e}")
        # Fallback to default context
        return ssl.create_default_context()

async def make_openai_request_with_ssl(api_key: str, payload: dict) -> dict:
    """Make OpenAI API request with proper SSL handling"""
    try:
        ssl_context = create_ssl_context()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(verify=ssl_context, timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API error: {response.text}"
                )
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def extract_expense_data_from_image(image_base64: str) -> Dict[str, Any]:
    """
    Send image to ChatGPT for expense data extraction using direct HTTP request
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": EXPENSE_EXTRACTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        # Make request with SSL handling
        response_data = await make_openai_request_with_ssl(api_key, payload)
        
        # Extract the JSON response
        content = response_data["choices"][0]["message"]["content"]
        
        # Try to parse the JSON response
        try:
            # Clean the response in case there's extra text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChatGPT processing failed: {str(e)}")

def validate_image_file(file: UploadFile) -> bool:
    """
    Validate uploaded image file
    """
    # Check file size (max 4MB for OpenAI)
    max_size = 4 * 1024 * 1024  # 4MB
    if file.size and file.size > max_size:
        return False
    
    # Check file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_types:
        return False
    
    return True

@app.post("/api/process-receipt", response_model=ExpenseResponse)
async def process_receipt(file: UploadFile = File(...)):
    """
    Main API endpoint: Upload receipt -> ChatGPT processing -> Return expense data
    """
    start_time = datetime.now()
    
    try:
        # Validate the uploaded file
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file. Please upload an image file (JPEG, PNG) under 4MB."
            )
        
        # Read and encode the image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Process with ChatGPT
        extracted_data = await extract_expense_data_from_image(image_base64)
        
        # Create expense data object
        expense_data = ExpenseData(**extracted_data)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ExpenseResponse(
            success=True,
            expense_data=expense_data,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        return ExpenseResponse(
            success=False,
            error=str(e),
            processing_time=processing_time
        )

@app.get("/api/test-openai")
async def test_openai():
    """
    Test OpenAI connection with SSL fix
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key found"}
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello, this is a test"}],
            "max_tokens": 20
        }
        
        response_data = await make_openai_request_with_ssl(api_key, payload)
        
        return {
            "success": True,
            "response": response_data["choices"][0]["message"]["content"],
            "model_used": response_data["model"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.get("/api/test-ssl")
async def test_ssl():
    """
    Test basic SSL connectivity
    """
    try:
        ssl_context = create_ssl_context()
        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            response = await client.get("https://httpbin.org/get")
            return {
                "success": True,
                "status_code": response.status_code,
                "ssl_working": True
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ssl_working": False
        }

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Expense Reporting MVP API",
        "version": "1.0.0",
        "endpoints": {
            "process_receipt": "POST /api/process-receipt",
            "test_openai": "GET /api/test-openai", 
            "test_ssl": "GET /api/test-ssl",
            "health": "GET /api/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)