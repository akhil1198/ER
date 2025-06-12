# main.py - FastAPI Backend with Chat Interface
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

app = FastAPI(title="Expense Chat API", version="2.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Data models
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

class ChatMessage(BaseModel):
    id: str
    type: str  # 'user', 'assistant', 'expense_data', 'image'
    content: str
    timestamp: datetime
    expense_data: Optional[ExpenseData] = None
    image_url: Optional[str] = None

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    current_expense: Optional[ExpenseData] = None
    created_at: datetime

# In-memory storage (use database in production)
chat_sessions: Dict[str, ChatSession] = {}
active_connections: Dict[str, WebSocket] = {}

# ChatGPT prompts
EXPENSE_EXTRACTION_PROMPT = """
You are an expense reporting assistant. Analyze this receipt image and extract expense information.

Extract the following information in JSON format:
- expense_type: Categorize as "Meals", "Travel", "Accommodation", "Transportation", "Office Supplies", "Software", or "Other"
- transaction_date: Date in YYYY-MM-DD format
- business_purpose: Infer likely business purpose
- travel_type: "Domestic", "International", or null
- meal_type: "Breakfast", "Lunch", "Dinner", "Snack", or null
- vendor: Business/vendor name
- city: City where transaction occurred
- country: Country where transaction occurred
- payment_type: "Credit Card", "Cash", "Bank Transfer", or "Other"
- amount: Total amount as number
- currency: Currency code (USD, EUR, etc.)
- allocate_to_another_business_unit: false
- business_unit: null
- comment: Additional notes

Return ONLY valid JSON. If information is unclear, use null.
"""

CHAT_CORRECTION_PROMPT = """
You are an expense reporting assistant helping users correct expense data. 

Current expense data:
{current_data}

User correction request: "{user_message}"

Please update the expense data based on the user's correction and return the updated JSON with the same structure. Only modify fields that the user specifically mentions. Keep all other fields unchanged.

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

async def correct_expense_data(current_data: ExpenseData, user_message: str) -> Dict[str, Any]:
    """Use ChatGPT to correct expense data based on user feedback"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_data_json = current_data.model_dump()
        prompt = CHAT_CORRECTION_PROMPT.format(
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

def create_chat_session() -> ChatSession:
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        session_id=session_id,
        created_at=datetime.now()
    )
    
    # Add welcome message
    welcome_message = ChatMessage(
        id=str(uuid.uuid4()),
        type="assistant",
        content="Hi! I'm your expense reporting assistant. Drop a receipt image here and I'll extract the expense information for you. You can then review and make any corrections needed!",
        timestamp=datetime.now()
    )
    session.messages.append(welcome_message)
    
    chat_sessions[session_id] = session
    return session

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
    return {"messages": session.messages}

@app.post("/api/chat/{session_id}/upload-receipt")
async def upload_receipt(session_id: str, file: UploadFile = File(...)):
    """Upload receipt and extract expense data"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    
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
            content="🔍 Analyzing your receipt... This may take a few seconds.",
            timestamp=datetime.now()
        )
        session.messages.append(processing_message)
        await send_message_to_client(session_id, processing_message)
        
        # Extract expense data
        extracted_data = await extract_expense_data_from_image(image_base64)
        expense_data = ExpenseData(**extracted_data)
        session.current_expense = expense_data
        
        # Add expense data message
        expense_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="expense_data",
            content="Here's what I extracted from your receipt. Please review and let me know if you'd like to make any changes:",
            timestamp=datetime.now(),
            expense_data=expense_data
        )
        session.messages.append(expense_message)
        await send_message_to_client(session_id, expense_message)
        
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
    """Send a text message and process corrections"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    user_text = message_data.get("content", "")
    
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
        # Check if user wants to correct current expense data
        if session.current_expense and any(keyword in user_text.lower() for keyword in 
                                         ['change', 'correct', 'update', 'fix', 'wrong', 'should be']):
            
            # Process correction with ChatGPT
            corrected_data = await correct_expense_data(session.current_expense, user_text)
            session.current_expense = ExpenseData(**corrected_data)
            
            # Send updated expense data
            correction_message = ChatMessage(
                id=str(uuid.uuid4()),
                type="expense_data",
                content="✅ I've updated the expense data based on your feedback:",
                timestamp=datetime.now(),
                expense_data=session.current_expense
            )
            session.messages.append(correction_message)
            await send_message_to_client(session_id, correction_message)
            
        else:
            # General chat response
            response_content = "I understand. "
            if not session.current_expense:
                response_content += "Please upload a receipt image so I can help you extract expense information."
            else:
                response_content += "Is there anything you'd like me to change about the current expense data? Or would you like to create the expense report?"
            
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
        "message": "Expense Chat API",
        "version": "2.0.0",
        "endpoints": {
            "create_session": "POST /api/chat/create-session",
            "upload_receipt": "POST /api/chat/{session_id}/upload-receipt",
            "send_message": "POST /api/chat/{session_id}/send-message",
            "websocket": "WS /ws/chat/{session_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)