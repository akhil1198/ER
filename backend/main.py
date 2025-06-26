# main.py - Simplified FastAPI Backend
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import openai
import base64
import json
import os
from datetime import datetime
import uuid

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Expense Chat API", version="4.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Data models
class SAPConcurExpense(BaseModel):
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

class MessageRequest(BaseModel):
    content: str

class MessageResponse(BaseModel):
    messages: List[ChatMessage]
    mode: str
    current_expense: Optional[SAPConcurExpense] = None

# In-memory storage
chat_sessions: Dict[str, ChatSession] = {}

# SAP Concur field mapping
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

def create_message(msg_type: str, content: str, expense_data: Optional[SAPConcurExpense] = None, image_url: Optional[str] = None) -> ChatMessage:
    """Helper function to create a message"""
    return ChatMessage(
        id=str(uuid.uuid4()),
        type=msg_type,
        content=content,
        timestamp=datetime.now(),
        expense_data=expense_data,
        image_url=image_url
    )

def validate_sap_concur_data(expense_data: SAPConcurExpense) -> Dict[str, str]:
    """Validate expense data against SAP Concur requirements"""
    errors = {}
    
    for field_name, field_config in SAP_CONCUR_FIELD_MAP.items():
        value = getattr(expense_data, field_name)
        
        if field_config.get("required") and (value is None or value == ""):
            errors[field_name] = f"{field_config['name']} is required"
        
        if value is not None and "valid_values" in field_config:
            if str(value) not in field_config["valid_values"]:
                errors[field_name] = f"{field_config['name']} must be one of: {', '.join(field_config['valid_values'])}"
    
    return errors

async def call_openai(messages: List[Dict], max_tokens: int = 1000, temperature: float = 0.1) -> str:
    """Helper function to call OpenAI API"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API failed: {str(e)}")

async def extract_expense_data_from_image(image_base64: str) -> Dict[str, Any]:
    """Extract expense data from receipt image"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": EXPENSE_EXTRACTION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        }
    ]
    
    content = await call_openai(messages)
    
    # Parse JSON response
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    if json_start != -1 and json_end != -1:
        json_str = content[json_start:json_end]
        return json.loads(json_str)
    else:
        raise HTTPException(status_code=500, detail="No valid JSON found in response")

async def correct_expense_data(current_data: SAPConcurExpense, user_message: str) -> Dict[str, Any]:
    """Correct expense data based on user feedback"""
    current_data_json = current_data.model_dump()
    prompt = CORRECTION_PROMPT.format(
        current_data=json.dumps(current_data_json, indent=2),
        user_message=user_message
    )
    
    messages = [{"role": "user", "content": prompt}]
    content = await call_openai(messages)
    
    # Parse JSON response
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    if json_start != -1 and json_end != -1:
        json_str = content[json_start:json_end]
        return json.loads(json_str)
    else:
        raise HTTPException(status_code=500, detail="No valid JSON found in correction response")

async def normal_chat_response(user_message: str) -> str:
    """Generate normal chat response"""
    messages = [
        {"role": "system", "content": NORMAL_CHAT_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    try:
        return await call_openai(messages, max_tokens=500, temperature=0.7)
    except:
        return "I apologize, but I'm having trouble processing your request right now. Please try again."

# API Endpoints
@app.post("/api/chat/create-session")
async def create_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        session_id=session_id,
        created_at=datetime.now(),
        mode="normal"
    )
    
    # Add welcome message
    welcome_message = create_message(
        "assistant", 
        "Hi! I'm your AI assistant. I can help you with expense reporting by analyzing receipt images, or we can just chat about anything you'd like. How can I help you today?"
    )
    session.messages.append(welcome_message)
    
    chat_sessions[session_id] = session
    return {"session_id": session.session_id}

@app.get("/api/chat/{session_id}/messages")
async def get_messages(session_id: str) -> MessageResponse:
    """Get all messages for a session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    return MessageResponse(
        messages=session.messages,
        mode=session.mode,
        current_expense=session.current_expense
    )

@app.post("/api/chat/{session_id}/upload-receipt")
async def upload_receipt(session_id: str, file: UploadFile = File(...)) -> MessageResponse:
    """Upload receipt and extract expense data"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    session.mode = "expense"
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:{file.content_type};base64,{image_base64}"
        
        # Add user image message
        user_message = create_message(
            "image", 
            f"Uploaded receipt: {file.filename}",
            image_url=image_url
        )
        session.messages.append(user_message)
        
        # Add processing message
        processing_message = create_message(
            "assistant",
            "Analyzing your receipt for SAP Concur... This may take a few seconds."
        )
        session.messages.append(processing_message)
        
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
        
        expense_message = create_message(
            "expense_data",
            expense_content,
            expense_data=expense_data
        )
        session.messages.append(expense_message)
        
        # Add validation message if there are errors
        if validation_errors:
            error_details = "\n".join([f"• {error}" for error in validation_errors.values()])
            validation_message = create_message(
                "assistant",
                f"📋 SAP Concur Requirements:\n{error_details}\n\nYou can ask me to fix these issues, like: 'Set the business purpose to client meeting' or 'Change the expense type to Meals'"
            )
            session.messages.append(validation_message)
        
        return MessageResponse(
            messages=session.messages,
            mode=session.mode,
            current_expense=session.current_expense
        )
        
    except Exception as e:
        error_message = create_message(
            "assistant",
            f"❌ Sorry, I had trouble processing your receipt: {str(e)}. Please try uploading again."
        )
        session.messages.append(error_message)
        
        return MessageResponse(
            messages=session.messages,
            mode=session.mode,
            current_expense=session.current_expense
        )

@app.post("/api/chat/{session_id}/send-message")
async def send_message(session_id: str, message_data: MessageRequest) -> MessageResponse:
    """Send a text message and get response"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    user_text = message_data.content.strip()
    
    # Add user message
    user_message = create_message("user", user_text)
    session.messages.append(user_message)
    
    try:
        # Check for exit commands
        exit_commands = ['stop', 'exit', 'quit', 'normal mode', 'regular chat']
        if any(cmd in user_text.lower() for cmd in exit_commands):
            session.mode = "normal"
            session.current_expense = None
            
            exit_message = create_message(
                "system",
                "✅ Switched to normal chat mode. We can now talk about anything! Upload a receipt if you want to process expenses again."
            )
            session.messages.append(exit_message)
            
        elif session.mode == "expense" and session.current_expense:
            # Check if user wants to correct expense data
            correction_keywords = ['change', 'correct', 'update', 'fix', 'set', 'modify', 'wrong', 'should be']
            if any(keyword in user_text.lower() for keyword in correction_keywords):
                
                # Process correction
                corrected_data = await correct_expense_data(session.current_expense, user_text)
                session.current_expense = SAPConcurExpense(**corrected_data)
                
                # Validate corrected data
                validation_errors = validate_sap_concur_data(session.current_expense)
                
                # Send updated expense data
                correction_content = "✅ I've updated the expense data:"
                if validation_errors:
                    correction_content += f"\n\n⚠️ {len(validation_errors)} SAP Concur requirement(s) still need attention."
                
                correction_message = create_message(
                    "expense_data",
                    correction_content,
                    expense_data=session.current_expense
                )
                session.messages.append(correction_message)
                
                # Send validation errors if any
                if validation_errors:
                    error_details = "\n".join([f"• {error}" for error in validation_errors.values()])
                    validation_message = create_message(
                        "assistant",
                        f"📋 Remaining SAP Concur Issues:\n{error_details}"
                    )
                    session.messages.append(validation_message)
            else:
                # General expense-related question
                response_content = "I understand. You can:\n• Make corrections like 'Change the vendor to Starbucks'\n• Ask 'What's required for SAP Concur?'\n• Say 'stop' to exit expense mode\n• Create the expense report when ready"
                
                assistant_message = create_message("assistant", response_content)
                session.messages.append(assistant_message)
        else:
            # Normal chat mode
            response_content = await normal_chat_response(user_text)
            assistant_message = create_message("assistant", response_content)
            session.messages.append(assistant_message)
            
    except Exception as e:
        error_message = create_message(
            "assistant",
            f"❌ Sorry, I had trouble processing your request: {str(e)}"
        )
        session.messages.append(error_message)
    
    return MessageResponse(
        messages=session.messages,
        mode=session.mode,
        current_expense=session.current_expense
    )

@app.get("/api/sap-concur/field-requirements")
async def get_sap_concur_requirements():
    """Get SAP Concur field requirements"""
    return {"fields": SAP_CONCUR_FIELD_MAP}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    return {
        "message": "Simplified Expense Chat API",
        "version": "4.0.0",
        "features": ["Normal Chat", "Expense Processing", "SAP Concur Integration"],
        "endpoints": {
            "create_session": "POST /api/chat/create-session",
            "upload_receipt": "POST /api/chat/{session_id}/upload-receipt",
            "send_message": "POST /api/chat/{session_id}/send-message",
            "sap_requirements": "GET /api/sap-concur/field-requirements"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)