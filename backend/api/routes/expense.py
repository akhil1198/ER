# backend/api/routes/expense.py - CLEANED VERSION

from fastapi import APIRouter, File, UploadFile, HTTPException, Path, Query
from typing import Dict, Any, Optional
import base64
import logging

# Model imports
from models.expense import (
    ExpenseData, 
    ExpenseEntryRequest, 
    EnhancedExpenseData, 
    EnhancedExpenseEntryRequest
)

from services.enhanced_openai_service import EnhancedOpenAIService
from services.enhanced_expense_service import EnhancedExpenseService

# Service imports - with fallback handling
from services.sap_service import SAPService
from services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["expense"])

# Logger setup
logger = logging.getLogger(__name__)

# Initialize services with proper error handling
def initialize_services():
    """Initialize services with fallback to basic services if enhanced ones fail"""
    openai_service = EnhancedOpenAIService()
    expense_service = EnhancedExpenseService()
    logger.info("✅ Enhanced services initialized successfully")
    return openai_service, expense_service, True

# Initialize services
openai_service, expense_service, has_enhanced_services = initialize_services()
sap_service = SAPService()
chat_service = ChatService()


@router.post("/process-receipt")
async def process_receipt(file: UploadFile = File(...)):
    """Process uploaded receipt with intelligent expense type detection"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload an image."
        )
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info("📷 Processing receipt image with intelligent categorization...")
        
        # Step 1: Extract data using improved prompt
        extraction_result = await openai_service.extract_expense_data(image_base64)
        print(f"******************Extraction Result: {extraction_result}")
        
        logger.info(f"🎯 Detected Category: {extraction_result.get('category')}")
        logger.info(f"🏷️ Detected Type: {extraction_result.get('expense_type')}")
        
        # Step 2: Map data to expense type using enhanced service
        if has_enhanced_services and hasattr(expense_service, 'map_data_to_expense_type'):
            mapping_result = await expense_service.map_data_to_expense_type(
                extraction_result.get('expense_type'), 
                extraction_result
            )
            logger.info("✅ Enhanced mapping successful")
        
        print(f"******************Mapping Result: {mapping_result.mapped_data}")
        
        # Step 3: Generate dynamic form configuration
        expense_type_id = extraction_result.get('expense_type', '').lower().replace(' ', '_')
        if has_enhanced_services and hasattr(expense_service, 'generate_expense_form'):
            form_config = expense_service.generate_expense_form(expense_type_id)
        else:
            form_config = {"expense_type": {"name": extraction_result.get('expense_type')}, "sections": []}
        
        # Step 4: Update chat service with mapped data
        _update_chat_service(mapping_result.mapped_data)
        
        # Step 5: Format validation errors
        validation_errors = []
        if hasattr(mapping_result, 'validation_errors'):
            validation_errors = [
                error if isinstance(error, dict) else {"field": "unknown", "message": str(error)}
                for error in mapping_result.validation_errors
            ]
        
        # Step 6: Create success message with detected information
        success_message = f"""🎉 **Receipt processed successfully!**

            🔍 **AI Detection Results:**
            • **Category**: {extraction_result.get('category', 'Unknown')}
            • **Expense Type**: {extraction_result.get('expense_type', 'Unknown')}

            📝 **Extracted Data:**
            I've intelligently mapped your receipt data to the appropriate fields for **{extraction_result.get('expense_type', 'this expense type')}**.
        """
        
        return {
            "success": True,
            "message": success_message,
            "expense_data": mapping_result.mapped_data,
            "expense_type_info": {
                "id": expense_type_id,
                "name": mapping_result.expense_type.name,
                "description": getattr(mapping_result.expense_type, 'description', 'Detected expense'),
                "category": getattr(mapping_result.expense_type, 'category', 'Other'),
                "form_config": form_config
            },
            "validation_errors": validation_errors,
            "next_action": "Review the extracted data below. You can edit any fields if needed, then choose what to do next:\n\n**1** - Create a new expense report\n**2** - Add to an existing report"
        }
        
    except Exception as e:
        logger.error(f"💥 Receipt processing error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process receipt: {str(e)}"
        )



@router.post("/confirm-expense-type")
async def confirm_expense_type(expense_data: EnhancedExpenseData):
    """Confirm and validate the selected expense type"""
    try:
        # Validate the expense data
        if has_enhanced_services and hasattr(expense_service, 'validate_expense_data'):
            validation_errors = expense_service.validate_expense_data(expense_data)
        else:
            validation_errors = []  # Basic validation can be added here
        
        if validation_errors:
            return {
                "success": False,
                "message": "Please fix the following errors:",
                "errors": validation_errors
            }
        
        # Update chat service with confirmed data
        chat_service.set_current_expense(expense_data)
        chat_service.update_conversation_state("waiting_for_choice")
        
        # Generate success message
        success_message = _generate_confirmation_message(expense_data)
        
        return {
            "success": True,
            "message": success_message,
            "expense_data": expense_data.dict(),
            "next_action": "Choose option 1 or 2 to continue"
        }
        
    except Exception as e:
        logger.error(f"Expense type confirmation error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to confirm expense type: {str(e)}"
        )


@router.get("/expense-types")
async def get_expense_types(category: str = Query(default="meals")):
    """Get available expense types for a category"""
    try:
        if has_enhanced_services and hasattr(expense_service, 'get_expense_types_by_category'):
            expense_types = expense_service.get_expense_types_by_category(category)
        else:
            expense_types = _get_basic_expense_types()
            
        return {
            "success": True,
            "category": category,
            "expense_types": expense_types
        }
    except Exception as e:
        logger.error(f"Error getting expense types: {str(e)}")
        return {
            "success": True,
            "category": category, 
            "expense_types": _get_basic_expense_types()
        }


@router.get("/expense-types/{expense_type_id}/form")
async def get_expense_type_form(expense_type_id: str = Path(...)):
    """Get dynamic form configuration for an expense type"""
    try:
        if has_enhanced_services and hasattr(expense_service, 'generate_expense_form'):
            form_config = expense_service.generate_expense_form(expense_type_id)
        else:
            form_config = _get_basic_form_config(expense_type_id)
            
        return {
            "success": True,
            "expense_type_id": expense_type_id,
            "form_config": form_config
        }
    except Exception as e:
        logger.error(f"Error getting expense type form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expense-entry")
async def create_expense_entry_endpoint(expense_data: ExpenseEntryRequest):
    """Create new expense entry (legacy endpoint)"""
    try:
        created_entry = await sap_service.create_expense_entry(expense_data)
        return {
            "success": True,
            "message": "Expense entry created successfully!",
            "entry": created_entry
        }
    except Exception as e:
        logger.error(f"Error creating expense entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-expense-to-report")
async def add_expense_to_report(report_id: str, expense_data: ExpenseData):
    """Add expense data to existing report (legacy endpoint)"""
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
        logger.error(f"Error adding expense to report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def _extract_expense_data(image_base64: str) -> Dict[str, Any]:
    """Extract expense data from image with fallback handling"""
    try:
        if has_enhanced_services and hasattr(openai_service, 'extract_expense_data_with_type'):
            extraction_result = await openai_service.extract_expense_data_with_type(image_base64)
            logger.info(f"✅ Enhanced extraction successful: {extraction_result['suggested_expense_type']}")
            return extraction_result
        else:
            # Fallback to basic extraction
            extraction_data = await openai_service.extract_expense_data(image_base64)
            logger.info("⚠️ Using basic extraction fallback")
            return {
                "suggested_expense_type": extraction_data.get('suggested_expense_type', 'meals_employee_in_town'),
                "expense_data": extraction_data,
                "classification_reasoning": "Basic extraction method"
            }
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        # Return error fallback
        return {
            "suggested_expense_type": "meals_employee_in_town",
            "expense_data": {
                "vendor": "Unknown Vendor",
                "transaction_date": "2024-01-01",
                "amount": 0.0,
                "currency": "USD",
                "city": "Unknown",
                "country": "US",
                "payment_type": "Credit Card",
                "meal_type": "lunch",
                "business_purpose": "Business meal",
                "comment": f"Extraction error: {str(e)}"
            },
            "classification_reasoning": "Error fallback"
        }


async def _map_expense_data(suggested_type: str, expense_data: Dict[str, Any]) -> Any:
    """Map expense data to expense type with fallback handling"""
    try:
        if has_enhanced_services and hasattr(expense_service, 'map_data_to_expense_type'):
            mapping_result = await expense_service.map_data_to_expense_type(suggested_type, expense_data)
            logger.info("✅ Enhanced mapping successful")
            return mapping_result
        else:
            # Basic fallback
            logger.info("⚠️ Using basic mapping fallback")
            return type('MappingResult', (), {
                'mapped_data': expense_data,
                'expense_type': type('ExpenseType', (), {
                    'name': suggested_type.replace('_', ' ').title(),
                    'description': 'Meal expense',
                    'sap_form': 'Basic Form'
                })(),
                'validation_errors': []
            })()
    except Exception as e:
        logger.error(f"❌ Mapping failed: {e}")
        # Return basic mapping result
        return type('MappingResult', (), {
            'mapped_data': expense_data,
            'expense_type': type('ExpenseType', (), {
                'name': suggested_type.replace('_', ' ').title(),
                'description': 'Meal expense',
                'sap_form': 'Basic Form'
            })(),
            'validation_errors': []
        })()


def _update_chat_service(mapped_data: Dict[str, Any]) -> None:
    """Update chat service state with expense data"""
    try:
        print("setting current expense data in chat service 111111111111111111111", mapped_data)
        enhanced_expense_data = ExpenseData(**mapped_data)
        print("setting current expense data in chat service 222222222222222222222", enhanced_expense_data)

        chat_service.set_current_expense(enhanced_expense_data)
        chat_service.update_conversation_state("waiting_for_choice")
        logger.info("✅ Chat service updated")
    except Exception as e:
        logger.warning(f"⚠️ Chat service update failed: {e}")


def _format_process_receipt_response(extraction_result: Dict[str, Any], mapping_result: Any) -> Dict[str, Any]:
    """Format the response for process_receipt endpoint"""
    # Format validation errors if available
    validation_errors = []
    if hasattr(mapping_result, 'validation_errors'):
        validation_errors = [
            error.to_dict() if hasattr(error, 'to_dict') else {"field": "unknown", "message": str(error)}
            for error in mapping_result.validation_errors
        ]
    
    # Generate form config
    suggested_type = extraction_result['suggested_expense_type']
    if has_enhanced_services and hasattr(expense_service, 'generate_expense_form'):
        form_config = expense_service.generate_expense_form(suggested_type)
    else:
        form_config = {"expense_type": {"name": suggested_type}, "sections": []}
    
    return {
        "success": True,
        "message": "🎉 **Receipt processed successfully!**\n\nI've intelligently mapped your receipt data to the appropriate fields.",
        "expense_data": mapping_result.mapped_data,
        "expense_type_info": {
            "id": suggested_type,
            "name": mapping_result.expense_type.name,
            "description": getattr(mapping_result.expense_type, 'description', 'Meal expense'),
            "form_config": form_config
        },
        "validation_errors": validation_errors,
        "next_action": "Review the extracted data below. You can edit any fields if needed, then choose what to do next:\n\n**1** - Create a new expense report\n**2** - Add to an existing report"
    }


def _generate_confirmation_message(expense_data: EnhancedExpenseData) -> str:
    """Generate confirmation message for expense type selection"""
    category_emoji = {
        "Meals & Entertainment": "🍽️",
        "Transportation": "🚗",
        "Lodging": "🏨", 
        "Office Supplies": "📎"
    }.get(expense_data.expense_category, "📋")
    
    success_message = f"✅ **Expense Type Confirmed!**\n\n{category_emoji} **Category:** {expense_data.expense_category}\n🎯 **Type:** {expense_data.expense_type}"
    
    # Add meal-specific details if applicable
    if expense_data.expense_category == "Meals & Entertainment":
        success_message += f"\n🍽️ **Meal Type:** {expense_data.meal_type}"
        success_message += f"\n👥 **Attendees:** {expense_data.attendees_count}"
        
        if expense_data.client_prospect_name:
            success_message += f"\n🏢 **Client/Prospect:** {expense_data.client_prospect_name}"
    
    success_message += f"\n📝 **Business Purpose:** {expense_data.business_purpose}"
    success_message += "\n\nWhat would you like to do next?\n\n**1** - Create a new expense report\n**2** - Add to an existing report"
    
    return success_message


def _get_basic_expense_types() -> list:
    """Get basic expense types as fallback"""
    return [
        {
            "id": "meals_employee_in_town",
            "name": "Meals Employee(s) Only - In Town",
            "description": "Meals with only company employees while in town",
            "sap_form": "AJG Non-VAT MealsEEOnly Attendees"
        },
        {
            "id": "meals_client_in_town", 
            "name": "Meals with Client(s) - In Town",
            "description": "Business meals with clients while in town",
            "sap_form": "AJG Non-VAT Client Meals w/ Attendees"
        },
        {
            "id": "meals_client_out_of_town",
            "name": "Meals with Client(s) - Out of Town", 
            "description": "Business meals with clients while traveling",
            "sap_form": "AJG Non-VAT Client Meals w/ Attendees+Trvl Type"
        },
        {
            "id": "meeting_catering",
            "name": "Meeting/Catering",
            "description": "Catering for business meetings",
            "sap_form": "AJG Non-VAT Meeting/Catering Attendees"
        }
    ]


def _get_basic_form_config(expense_type_id: str) -> Dict[str, Any]:
    """Get basic form configuration as fallback"""
    return {
        "expense_type": {
            "id": expense_type_id,
            "name": expense_type_id.replace('_', ' ').title(),
            "description": "Meal expense",
            "sap_form": "Basic Form"
        },
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "vendor_description", "type": "text", "label": "Vendor", "required": True},
                    {"name": "amount", "type": "money", "label": "Amount", "required": True},
                    {"name": "transaction_date", "type": "date", "label": "Date", "required": True},
                    {"name": "business_purpose", "type": "textarea", "label": "Business Purpose", "required": True}
                ]
            }
        ]
    }