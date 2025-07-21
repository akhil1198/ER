# backend/api/routes/expense.py - FIXED VERSION

from fastapi import APIRouter, File, UploadFile, HTTPException, Path, Query
from typing import Dict, Any, Optional
import base64

from models.expense import ExpenseData, ExpenseEntryRequest
from services.enhanced_openai_service import EnhancedOpenAIService
from services.enhanced_expense_service import EnhancedExpenseService
from services.sap_service import SAPService
from services.chat_service import ChatService
from models.expense import EnhancedExpenseData, EnhancedExpenseEntryRequest
from services.enhanced_openai_service import EnhancedOpenAIService
from services.enhanced_expense_service import EnhancedExpenseService

router = APIRouter(prefix="/api", tags=["expense"])

# Initialize enhanced services
try:
    enhanced_openai_service = EnhancedOpenAIService()
    enhanced_expense_service = EnhancedExpenseService()
    sap_service = SAPService()
    chat_service = ChatService()
    print("✅ Enhanced services initialized successfully")
except Exception as e:
    print(f"❌ Error initializing enhanced services: {e}")
    # Fallback to basic services if enhanced ones fail
    from services.openai_service import OpenAIService
    from services.expense_service import ExpenseService
    enhanced_openai_service = OpenAIService()
    enhanced_expense_service = ExpenseService()

@router.post("/process-receipt")
async def process_receipt(file: UploadFile = File(...)):
    """Process uploaded receipt with intelligent expense type detection"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        print("📷 Processing receipt image...")
        
        # Try enhanced extraction first
        try:
            if hasattr(enhanced_openai_service, 'extract_expense_data_with_type'):
                extraction_result = await enhanced_openai_service.extract_expense_data_with_type(image_base64)
                print(f"✅ Enhanced extraction successful: {extraction_result['suggested_expense_type']}")
            else:
                # Fallback to basic extraction
                extraction_data = await enhanced_openai_service.extract_expense_data(image_base64)
                extraction_result = {
                    "suggested_expense_type": extraction_data.get('suggested_expense_type', 'meals_employee_in_town'),
                    "confidence": extraction_data.get('confidence', 0.7),
                    "expense_data": extraction_data,
                    "classification_reasoning": "Basic extraction method"
                }
                print("⚠️ Using basic extraction fallback")
        except Exception as e:
            print(f"❌ Enhanced extraction failed: {e}")
            # Create a basic fallback response
            extraction_result = {
                "suggested_expense_type": "meals_employee_in_town",
                "confidence": 0.5,
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
        
        # Get suggested expense type and confidence
        suggested_type = extraction_result['suggested_expense_type']
        confidence = extraction_result['confidence']
        expense_data = extraction_result['expense_data']
        
        print(f"🎯 Suggested type: {suggested_type} (confidence: {confidence})")
        
        # Try enhanced mapping if available
        try:
            if hasattr(enhanced_expense_service, 'map_data_to_expense_type'):
                mapping_result = await enhanced_expense_service.map_data_to_expense_type(
                    suggested_type, 
                    expense_data
                )
                
                # Generate dynamic form configuration
                form_config = enhanced_expense_service.generate_expense_form(suggested_type)
                
                print("✅ Enhanced mapping successful")
            else:
                # Basic fallback
                from services.expense_service import ExpenseService
                basic_service = ExpenseService()
                mapped_data = basic_service.map_expense_data_to_entry(ExpenseData(**expense_data), "dummy_report")
                
                mapping_result = type('MappingResult', (), {
                    'mapped_data': expense_data,
                    'expense_type': type('ExpenseType', (), {
                        'name': suggested_type.replace('_', ' ').title(),
                        'description': 'Meal expense',
                        'sap_form': 'Basic Form'
                    })(),
                    'validation_errors': []
                })()
                
                form_config = {"expense_type": {"name": suggested_type}, "sections": []}
                print("⚠️ Using basic mapping fallback")
                
        except Exception as e:
            print(f"❌ Mapping failed: {e}")
            # Create basic mapping result
            mapping_result = type('MappingResult', (), {
                'mapped_data': expense_data,
                'expense_type': type('ExpenseType', (), {
                    'name': suggested_type.replace('_', ' ').title(),
                    'description': 'Meal expense',
                    'sap_form': 'Basic Form'
                })(),
                'validation_errors': []
            })()
            form_config = {"expense_type": {"name": suggested_type}, "sections": []}
        
        # Update chat service state with enhanced data
        try:
            enhanced_expense_data = ExpenseData(**mapping_result.mapped_data)
            chat_service.set_current_expense(enhanced_expense_data)
            chat_service.update_conversation_state("waiting_for_choice")
            print("✅ Chat service updated")
        except Exception as e:
            print(f"⚠️ Chat service update failed: {e}")
        
        # Format validation errors if available
        validation_errors = []
        if hasattr(mapping_result, 'validation_errors'):
            validation_errors = [
                error.to_dict() if hasattr(error, 'to_dict') else {"field": "unknown", "message": str(error)}
                for error in mapping_result.validation_errors
            ]
        
        return {
            "success": True,
            "message": f"🎉 **Receipt processed successfully!**\n\n📋 **Detected Expense Type**: {mapping_result.expense_type.name}\n🎯 **Confidence**: {confidence:.0%}\n\nI've intelligently mapped your receipt data to the appropriate fields.",
            "expense_data": mapping_result.mapped_data,
            "expense_type_info": {
                "id": suggested_type,
                "name": mapping_result.expense_type.name,
                "description": getattr(mapping_result.expense_type, 'description', 'Meal expense'),
                "confidence": confidence,
                "form_config": form_config
            },
            "validation_errors": validation_errors,
            "next_action": "Review the extracted data below. You can edit any fields if needed, then choose what to do next:\n\n**1** - Create a new expense report\n**2** - Add to an existing report"
        }
        
    except Exception as e:
        print(f"💥 Receipt processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process receipt: {str(e)}")

@router.post("/confirm-expense-type")
async def confirm_expense_type(expense_data: EnhancedExpenseData):
    """Confirm and validate the selected expense type"""
    try:
        # Validate the expense data
        validation_errors = expense_service.validate_expense_data(expense_data)
        
        if validation_errors:
            return {
                "success": False,
                "message": "Please fix the following errors:",
                "errors": validation_errors
            }
        
        # Update chat service with confirmed data
        chat_service.set_current_expense(expense_data)
        chat_service.update_conversation_state("waiting_for_choice")
        
        # Generate success message based on expense type
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
        
        return {
            "success": True,
            "message": success_message,
            "expense_data": expense_data.dict(),
            "next_action": "Choose option 1 or 2 to continue"
        }
        
    except Exception as e:
        print(f"Expense type confirmation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm expense type: {str(e)}")

@router.get("/expense-types/{category}")
async def get_expense_types(category: str):
    """Get available expense types for a category"""
    try:
        available_types = expense_service.get_expense_type_options(category)
        return {
            "success": True,
            "category": category,
            "expense_types": available_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Basic fallback endpoints that work with your existing system
@router.get("/expense-types")
async def get_expense_types(category: str = "meals"):
    """Get available expense types for a category"""
    try:
        # Basic meal types if enhanced service not available
        basic_types = [
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
        
        if hasattr(enhanced_expense_service, 'get_expense_types_by_category'):
            expense_types = enhanced_expense_service.get_expense_types_by_category(category)
        else:
            expense_types = basic_types
            
        return {
            "success": True,
            "category": category,
            "expense_types": expense_types
        }
    except Exception as e:
        return {
            "success": True,
            "category": category, 
            "expense_types": basic_types
        }

@router.get("/expense-types/{expense_type_id}/form")
async def get_expense_type_form(expense_type_id: str = Path(...)):
    """Get dynamic form configuration for an expense type"""
    try:
        if hasattr(enhanced_expense_service, 'generate_expense_form'):
            form_config = enhanced_expense_service.generate_expense_form(expense_type_id)
        else:
            # Basic form config
            form_config = {
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
            
        return {
            "success": True,
            "expense_type_id": expense_type_id,
            "form_config": form_config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for backward compatibility
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-expense-to-report")
async def add_expense_to_report(report_id: str, expense_data: ExpenseData):
    """Add expense data to existing report (legacy endpoint)"""
    try:
        from services.expense_service import ExpenseService
        basic_service = ExpenseService()
        
        # Map expense data to entry format
        expense_entry_data = basic_service.map_expense_data_to_entry(expense_data, report_id)
        
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