from fastapi import APIRouter, File, UploadFile, HTTPException
from models.expense import ExpenseData, ExpenseEntryRequest
from services import OpenAIService, SAPService, ExpenseService, ChatService
import base64

router = APIRouter(prefix="/api", tags=["expense"])

# Initialize services
openai_service = OpenAIService()
sap_service = SAPService()
expense_service = ExpenseService()
chat_service = ChatService()

@router.post("/process-receipt")
async def process_receipt(file: UploadFile = File(...)):
    """Process uploaded receipt and extract expense data"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Extract expense data using OpenAI
        extracted_data = await openai_service.extract_expense_data(image_base64)
        expense_data = ExpenseData(**extracted_data)
        
        # Update chat service state
        chat_service.set_current_expense(expense_data)
        chat_service.update_conversation_state("waiting_for_choice")
        
        return {
            "success": True,
            "message": "🎉 **Receipt processed successfully!**\n\nHere's what I extracted from your receipt:",
            "expense_data": expense_data.dict(),
            "next_action": "What would you like to do next?\n\n**1** - Create a new expense report\n**2** - Add to an existing report\n\nJust type **1** or **2** to continue!"
        }
        
    except Exception as e:
        print(f"Receipt processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process receipt: {str(e)}")

@router.post("/expense-entry")
async def create_expense_entry_endpoint(expense_data: ExpenseEntryRequest):
    """Create new expense entry"""
    try:
        created_entry = await sap_service.create_expense_entry(expense_data)
        return {
            "success": True,
            "message": "Expense entry created successfully!",
            "entry": created_entry
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-expense-to-report")
async def add_expense_to_report(report_id: str, expense_data: ExpenseData):
    """Add expense data to existing report"""
    try:
        # Map expense data to entry format
        expense_entry_data = expense_service.map_expense_data_to_entry(expense_data, report_id)
        
        # Create the expense entry
        created_entry = await sap_service.create_expense_entry(expense_entry_data)
        
        return {
            "success": True,
            "message": "Expense added to report successfully!",
            "entry": created_entry,
            "expense_details": {
                "vendor": expense_entry_data.vendor_description,
                "amount": expense_entry_data.transaction_amount,
                "currency": expense_entry_data.transaction_currency_code,
                "date": expense_entry_data.transaction_date,
                "description": expense_entry_data.description
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))