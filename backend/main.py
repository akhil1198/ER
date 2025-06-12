# main.py - FastAPI Backend with Enhanced Chat Features
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import openai
import base64
import json
import os
from datetime import datetime
import uuid
import asyncio

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Expense Chat API", version="3.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Both CRA and Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Data models - SAP Concur compliant
class SAPConcurExpense(BaseModel):
    expense_type: Optional[str] = None  # Required: Expense Type
    transaction_date: Optional[str] = None  # Required: Transaction Date (YYYY-MM-DD)
    business_purpose: Optional[str] = None  # Required: Business Purpose
    travel_type: Optional[str] = None  # Travel Type (if applicable)
    meal_type: Optional[str] = None  # Meal Type (if applicable)
    vendor: Optional[str] = None  # Required: Vendor
    city: Optional[str] = None  # Required: City
    country: Optional[str] = None  # Required: Country
    payment_type: Optional[str] = None  # Required: Payment Type
    amount: Optional[float] = None  # Required: Amount
    currency: Optional[str] = None  # Required: Currency
    allocate_to_another_business_unit: Optional[bool] = False  # Allocate to Another Business Unit
    business_unit: Optional[str] = None  # Business Unit
    comment: Optional[str] = None  # Comment

class ChatMessage(BaseModel):
    id: str
    type: str  # 'user', 'assistant', 'expense_data', 'image', 'system'
    content: str
    timestamp: datetime
    expense_data: Optional[SAPConcurExpense] = None
    image_url: Optional[str] = None

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    current_expense: Optional[SAPConcurExpense] = None
    mode: str = "normal"  # "normal" or "expense"
    created_at: datetime

# In-memory storage (use database in production)
chat_sessions: Dict[str, ChatSession] = {}
active_connections: Dict[str, WebSocket] = {}

# SAP Concur field mapping and validation
SAP_CONCUR_FIELD_MAP = {
    "expense_type": {
        "name": "Expense Type",
        "required": True,
        "valid_values": ["Meals", "Travel", "Accommodation", "Transportation", "Office Supplies", "Software", "Entertainment", "Fuel", "Parking", "Other"],
        "description": "Category of expense"
    },
    "transaction_date": {
        "name": "Transaction Date",
        "required": True,
        "format": "YYYY-MM-DD",
        "description": "Date when the transaction occurred"
    },
    "business_purpose": {
        "name": "Business Purpose",
        "required": True,
        "description": "Reason for the business expense"
    },
    "travel_type": {
        "name": "Travel Type",
        "required": False,
        "valid_values": ["Domestic", "International"],
        "description": "Type of travel (if applicable)"
    },
    "meal_type": {
        "name": "Meal Type",
        "required": False,
        "valid_values": ["Breakfast", "Lunch", "Dinner", "Snack", "Other"],
        "description": "Type of meal (if applicable)"
    },
    "vendor": {
        "name": "Vendor",
        "required": True,
        "description": "Name of the business/vendor"
    },
    "city": {
        "name": "City",
        "required": True,
        "description": "City where transaction occurred"
    },
    "country": {
        "name": "Country",
        "required": True,
        "description": "Country where transaction occurred"
    },
    "payment_type": {
        "name": "Payment Type",
        "required": True,
        "valid_values": ["Credit Card", "Cash", "Bank Transfer", "Check", "Other"],
        "description": "Method of payment"
    },
    "amount": {
        "name": "Amount",
        "required": True,
        "type": "number",
        "description": "Total amount of the expense"
    },
    "currency": {
        "name": "Currency",
        "required": True,
        "valid_values": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR"],
        "description": "Currency code"
    },
    "allocate_to_another_business_unit": {
        "name": "Allocate to Another Business Unit",
        "required": False,
        "type": "boolean",
        "description": "Whether to allocate to another business unit"
    },
    "business_unit": {
        "name": "Business Unit",
        "required": False,
        "description": "Business unit to allocate expense to"
    },
    "comment": {
        "name": "Comment",
        "required": False,
        "description": "Additional comments or notes"
    }
}

# ChatGPT prompts
EXPENSE_EXTRACTION_PROMPT = """
You are an expense reporting assistant. Analyze this receipt image and extract expense information for SAP Concur.

Map the information to these exact SAP Concur fields:

REQUIRED FIELDS:
- expense_type: Choose from ["Meals", "Travel", "Accommodation", "Transportation", "Office Supplies", "Software", "Entertainment", "Fuel", "Parking", "Other"]
- transaction_date: Date in YYYY-MM-DD format
- business_purpose: Infer likely business purpose
- vendor: Business/vendor name from receipt
- city: City where transaction occurred
- country: Country where transaction occurred  
- payment_type: Choose from ["Credit Card", "Cash", "Bank Transfer", "Check", "Other"]
- amount: Total amount as number
- currency: Currency code from ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR"]

OPTIONAL FIELDS:
- travel_type: "Domestic" or "International" (only if travel-related)
- meal_type: Choose from ["Breakfast", "Lunch", "Dinner", "Snack", "Other"] (only if meal)
- allocate_to_another_business_unit: false (default)
- business_unit: null (default)
- comment: Additional itemized details or notes

Return ONLY valid JSON with these exact field names. Use null for missing optional fields.

Example:
{
  "expense_type": "Meals",
  "transaction_date": "2024-06-12",
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
  "comment": "Business lunch with potential client to discuss partnership opportunities"
}
"""

NORMAL_CHAT_PROMPT = """
You are a helpful AI assistant. The user has exited expense reporting mode and wants to have a normal conversation. 

Respond naturally and helpfully to their questions. You can discuss any topics, provide information, help with tasks, or just chat casually.

If they want to go back to expense reporting, they can upload a receipt image or say something like "help me with expenses" or "process a receipt".
"""

CORRECTION_PROMPT = """
You are an expense reporting assistant helping users correct SAP Concur expense data.

Current expense data:
{current_data}

User wants to make this change: "{user_message}"

Update the expense data based on the user's request. Only modify the specific fields mentioned. Keep all other fields unchanged.

SAP Concur field constraints:
- expense_type: Must be one of ["Meals", "Travel", "Accommodation", "Transportation", "Office Supplies", "Software", "Entertainment", "Fuel", "Parking", "Other"]
- transaction_date: Must be YYYY-MM-DD format
- travel_type: "Domestic" or "International" or null
- meal_type: One of ["Breakfast", "Lunch", "Dinner", "Snack", "Other"] or null
- payment_type: One of ["Credit Card", "Cash", "Bank Transfer", "Check", "Other"]
- currency: Must be valid currency code like "USD", "EUR", etc.
- amount: Must be a number
- allocate_to_another_business_unit: true or false

Return ONLY the updated JSON with all fields included.
"""

async def extract_expense_data_from_image(image_base64: str) -> Dict[str, Any]:
    """Extract expense data from receipt image using ChatGPT"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
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
            max_tokens=1000,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in response")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChatGPT processing failed: {str(e)}")

async def correct_expense_data(current_data: SAPConcurExpense, user_message: str) -> Dict[str, Any]:
    """Use ChatGPT to correct expense data based on user feedback"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_data_json = current_data.model_dump()
        prompt = CORRECTION_PROMPT.format(
            current_data=json.dumps(current_data_json, indent=2),
            user_message=user_message
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in response")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correction failed: {str(e)}")

async def normal_chat_response(user_message: str) -> str:
    """Generate normal chat response using ChatGPT"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": NORMAL_CHAT_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I apologize, but I'm having trouble processing your request right now. Please try again."

def create_chat_session() -> ChatSession:
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        session_id=session_id,
        created_at=datetime.now(),
        mode="normal"
    )
    
    # Add welcome message
    welcome_message = ChatMessage(
        id=str(uuid.uuid4()),
        type="assistant",
        content="Hi! I'm your AI assistant. I can help you with expense reporting by analyzing receipt images, or we can just chat about anything you'd like. How can I help you today?",
        timestamp=datetime.now()
    )
    session.messages.append(welcome_message)
    
    chat_sessions[session_id] = session
    return session

def validate_sap_concur_data(expense_data: SAPConcurExpense) -> Dict[str, str]:
    """Validate expense data against SAP Concur requirements"""
    errors = {}
    
    for field_name, field_config in SAP_CONCUR_FIELD_MAP.items():
        value = getattr(expense_data, field_name)
        
        # Check required fields
        if field_config.get("required") and (value is None or value == ""):
            errors[field_name] = f"{field_config['name']} is required"
        
        # Check valid values
        if value is not None and "valid_values" in field_config:
            if str(value) not in field_config["valid_values"]:
                errors[field_name] = f"{field_config['name']} must be one of: {', '.join(field_config['valid_values'])}"
    
    return errors

async def send_message_to_client(session_id: str, message: ChatMessage):
    """Send message to connected WebSocket client"""
    if session_id in active_connections:
        try:
            await active_connections[session_id].send_text(message.model_dump_json())
        except:
            # Remove disconnected client
            del active_connections[session_id]

# REST API Endpoints
@app.post("/api/chat/create-session")
async def create_session():
    """Create a new chat session"""
    session = create_chat_session()
    return {"session_id": session.session_id}

@app.get("/api/chat/{session_id}/messages")
async def get_chat_messages(session_id: str):
    """Get all messages for a chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    return {"messages": session.messages, "mode": session.mode}

@app.post("/api/chat/{session_id}/upload-receipt")
async def upload_receipt(session_id: str, file: UploadFile = File(...)):
    """Upload receipt and extract expense data"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    
    # Switch to expense mode
    session.mode = "expense"
    
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:{file.content_type};base64,{image_base64}"
        
        # Add user message for image upload
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="image",
            content=f"Uploaded receipt: {file.filename}",
            timestamp=datetime.now(),
            image_url=image_url
        )
        session.messages.append(user_message)
        await send_message_to_client(session_id, user_message)
        
        # Add processing message
        processing_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="assistant",
            content="🔍 Analyzing your receipt for SAP Concur... This may take a few seconds.",
            timestamp=datetime.now()
        )
        session.messages.append(processing_message)
        await send_message_to_client(session_id, processing_message)
        
        # Extract expense data
        extracted_data = await extract_expense_data_from_image(image_base64)
        expense_data = SAPConcurExpense(**extracted_data)
        session.current_expense = expense_data
        
        # Validate data
        validation_errors = validate_sap_concur_data(expense_data)
        
        # Add expense data message
        expense_content = "Here's what I extracted from your receipt for SAP Concur:"
        if validation_errors:
            expense_content += f"\n\n⚠️ Please note: {len(validation_errors)} field(s) need attention for SAP Concur compliance."
        
        expense_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="expense_data",
            content=expense_content,
            timestamp=datetime.now(),
            expense_data=expense_data
        )
        session.messages.append(expense_message)
        await send_message_to_client(session_id, expense_message)
        
        # Add validation message if there are errors
        if validation_errors:
            error_details = "\n".join([f"• {error}" for error in validation_errors.values()])
            validation_message = ChatMessage(
                id=str(uuid.uuid4()),
                type="assistant",
                content=f"📋 SAP Concur Requirements:\n{error_details}\n\nYou can ask me to fix these issues, like: 'Set the business purpose to client meeting' or 'Change the expense type to Meals'",
                timestamp=datetime.now()
            )
            session.messages.append(validation_message)
            await send_message_to_client(session_id, validation_message)
        
        return {"success": True, "message": "Receipt processed successfully"}
        
    except Exception as e:
        error_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="assistant",
            content=f"❌ Sorry, I had trouble processing your receipt: {str(e)}. Please try uploading again.",
            timestamp=datetime.now()
        )
        session.messages.append(error_message)
        await send_message_to_client(session_id, error_message)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{session_id}/send-message")
async def send_message(session_id: str, message_data: dict):
    """Send a text message and process based on mode"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    user_text = message_data.get("content", "").strip()
    
    # Add user message
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        type="user",
        content=user_text,
        timestamp=datetime.now()
    )
    session.messages.append(user_message)
    await send_message_to_client(session_id, user_message)
    
    try:
        # Check for exit commands
        exit_commands = ['stop', 'exit', 'quit', 'normal mode', 'regular chat']
        if any(cmd in user_text.lower() for cmd in exit_commands):
            session.mode = "normal"
            session.current_expense = None
            
            exit_message = ChatMessage(
                id=str(uuid.uuid4()),
                type="system",
                content="✅ Switched to normal chat mode. We can now talk about anything! Upload a receipt if you want to process expenses again.",
                timestamp=datetime.now()
            )
            session.messages.append(exit_message)
            await send_message_to_client(session_id, exit_message)
            return {"success": True, "mode": "normal"}
        
        # Process based on current mode
        if session.mode == "expense" and session.current_expense:
            # Check if user wants to correct expense data
            correction_keywords = ['change', 'correct', 'update', 'fix', 'set', 'modify', 'wrong', 'should be']
            if any(keyword in user_text.lower() for keyword in correction_keywords):
                
                # Process correction with ChatGPT
                corrected_data = await correct_expense_data(session.current_expense, user_text)
                session.current_expense = SAPConcurExpense(**corrected_data)
                
                # Validate corrected data
                validation_errors = validate_sap_concur_data(session.current_expense)
                
                # Send updated expense data
                correction_content = "✅ I've updated the expense data:"
                if validation_errors:
                    correction_content += f"\n\n⚠️ {len(validation_errors)} SAP Concur requirement(s) still need attention."
                
                correction_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    type="expense_data",
                    content=correction_content,
                    timestamp=datetime.now(),
                    expense_data=session.current_expense
                )
                session.messages.append(correction_message)
                await send_message_to_client(session_id, correction_message)
                
                # Send validation errors if any
                if validation_errors:
                    error_details = "\n".join([f"• {error}" for error in validation_errors.values()])
                    validation_message = ChatMessage(
                        id=str(uuid.uuid4()),
                        type="assistant",
                        content=f"📋 Remaining SAP Concur Issues:\n{error_details}",
                        timestamp=datetime.now()
                    )
                    session.messages.append(validation_message)
                    await send_message_to_client(session_id, validation_message)
            else:
                # General expense-related question
                response_content = "I understand. You can:\n• Make corrections like 'Change the vendor to Starbucks'\n• Ask 'What's required for SAP Concur?'\n• Say 'stop' to exit expense mode\n• Create the expense report when ready"
                
                assistant_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    type="assistant",
                    content=response_content,
                    timestamp=datetime.now()
                )
                session.messages.append(assistant_message)
                await send_message_to_client(session_id, assistant_message)
        else:
            # Normal chat mode
            response_content = await normal_chat_response(user_text)
            
            assistant_message = ChatMessage(
                id=str(uuid.uuid4()),
                type="assistant",
                content=response_content,
                timestamp=datetime.now()
            )
            session.messages.append(assistant_message)
            await send_message_to_client(session_id, assistant_message)
            
    except Exception as e:
        error_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="assistant",
            content=f"❌ Sorry, I had trouble processing your request: {str(e)}",
            timestamp=datetime.now()
        )
        session.messages.append(error_message)
        await send_message_to_client(session_id, error_message)

@app.get("/api/sap-concur/field-requirements")
async def get_sap_concur_requirements():
    """Get SAP Concur field requirements"""
    return {"fields": SAP_CONCUR_FIELD_MAP}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    return {
        "message": "Enhanced Expense Chat API",
        "version": "3.0.0",
        "features": ["Normal Chat", "Expense Processing", "SAP Concur Integration", "Real-time Corrections"],
        "endpoints": {
            "create_session": "POST /api/chat/create-session",
            "upload_receipt": "POST /api/chat/{session_id}/upload-receipt",
            "send_message": "POST /api/chat/{session_id}/send-message",
            "sap_requirements": "GET /api/sap-concur/field-requirements",
            "websocket": "WS /ws/chat/{session_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)