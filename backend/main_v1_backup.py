# main.py - Updated FastAPI Backend for Expense Processing with Tax Compliance
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import openai
import base64
import json
import os
import requests
from datetime import datetime
import re

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Expense Chat API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
SAP_BASE_URL = "https://us2.api.concursolutions.com"
SAP_BEARER_TOKEN = os.getenv("SAP_BEARER_TOKEN")
SAP_USER_ID = "9e4f220f-b716-4738-9105-1153e04188ae"
SAP_USER_LOGIN = "24FE8B14@GALLAGHER.uat"

# Data models
class ChatMessage(BaseModel):
    content: str

class ExpenseData(BaseModel):
    expense_type: Optional[str] = None
    transaction_date: Optional[str] = None
    business_purpose: Optional[str] = None
    vendor: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    payment_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    comment: Optional[str] = None

class ReportCreateRequest(BaseModel):
    name: str
    business_purpose: str
    comment: Optional[str] = ""
    country_code: str = "US"
    country_subdivision_code: str = "US-WA"
    gift_policy_compliance: Optional[bool] = False  # New field for custom16
    irs_tax_policy_compliance: Optional[bool] = False  # New field for custom6

class ExpenseEntryRequest(BaseModel):
    report_id: str
    expense_type_code: str = "01028"  # Default expense type
    transaction_date: str
    transaction_amount: float
    transaction_currency_code: str = "USD"
    payment_type_id: str = "gWuT0oX4FNnukaeUcpOO3WSub$p5tY"  # Default payment type
    description: str
    vendor_description: str
    location_id: str = "D23A4483615E4A2084260E97E5F0D5E0"  # Default location (Miami)
    location_name: str = "Miami, Florida"
    location_city: str = "Miami"
    location_country_subdivision: str = "US-FL"
    location_country: str = "US"
    is_personal: bool = False
    is_billable: bool = False
    tax_receipt_type: str = "R"

async def create_expense_entry(expense_data: ExpenseEntryRequest) -> Dict:
    """Create new expense entry in SAP Concur"""
    try:
        url = f"{SAP_BASE_URL}/api/v3.0/expense/entries?user={SAP_USER_LOGIN}"
        headers = get_sap_headers()
        
        # Validate and sanitize data before sending
        description = expense_data.description[:64] if expense_data.description else "Business expense"
        vendor_description = expense_data.vendor_description[:64] if expense_data.vendor_description else "Vendor"
        
        payload = {
            "ReportID": expense_data.report_id,
            "ExpenseTypeCode": expense_data.expense_type_code,
            "TransactionDate": expense_data.transaction_date,
            "TransactionAmount": expense_data.transaction_amount,
            "TransactionCurrencyCode": expense_data.transaction_currency_code,
            "PaymentTypeID": expense_data.payment_type_id,
            "Description": description,
            "VendorDescription": vendor_description,
            "location": {
                "id": expense_data.location_id,
                "name": expense_data.location_name,
                "city": expense_data.location_city,
                "countrySubDivisionCode": expense_data.location_country_subdivision,
                "countryCode": expense_data.location_country
            },
            "IsPersonal": expense_data.is_personal,
            "IsBillable": expense_data.is_billable,
            "TaxReceiptType": expense_data.tax_receipt_type
        }
        
        print(f"Creating expense entry at: {url}")  # Debug log
        print(f"Payload: {json.dumps(payload, indent=2)}")  # Debug log
        print(f"Description length: {len(description)}")  # Debug log
        print(f"Vendor description length: {len(vendor_description)}")  # Debug log
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Create Expense Response Status: {response.status_code}")  # Debug log
        print(f"Create Expense Response: {response.text}")  # Debug log
        
        if response.status_code == 400:
            # Parse the error message for better user feedback
            try:
                error_data = response.json()
                error_message = error_data.get('Message', 'Bad Request')
                print(f"SAP API Error: {error_message}")
                raise HTTPException(status_code=400, detail=f"SAP Concur API error: {error_message}")
            except (json.JSONDecodeError, KeyError):
                raise HTTPException(status_code=400, detail=f"SAP Concur API error: {response.text}")
        
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"SAP Create Expense Entry Error: {str(e)}")  # Debug log
        error_detail = f"Failed to create expense entry: {str(e)}"
        
        # Extract more specific error info if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if 'Message' in error_data:
                    error_detail = f"SAP Concur error: {error_data['Message']}"
            except:
                pass
                
        raise HTTPException(status_code=500, detail=error_detail)

def map_expense_data_to_entry(expense_data: ExpenseData, report_id: str) -> ExpenseEntryRequest:
    """Map extracted expense data to SAP Concur expense entry format"""
    
    # Map expense types to SAP codes
    expense_type_mapping = {
        "meals": "01028",
        "travel": "01001", 
        "accommodation": "01002",
        "transportation": "01003",
        "office supplies": "01004",
        "software": "01005",
        "entertainment": "01006",
        "fuel": "01007",
        "parking": "01008",
        "other": "01028"
    }
    
    # Map payment types 
    payment_type_mapping = {
        "credit card": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "cash": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY", # Using same for demo
        "bank transfer": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "check": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "other": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY"
    }
    
    # Get expense type code
    expense_type_key = (expense_data.expense_type or "other").lower()
    expense_type_code = expense_type_mapping.get(expense_type_key, "01028")
    
    # Get payment type ID
    payment_type_key = (expense_data.payment_type or "credit card").lower()
    payment_type_id = payment_type_mapping.get(payment_type_key, "gWuT0oX4FNnukaeUcpOO3WSub$p5tY")
    
    # Create description with SAP Concur length limits (64 characters max)
    description_parts = []
    if expense_data.business_purpose:
        description_parts.append(expense_data.business_purpose)
    
    # If no business purpose, use a simple description
    if not description_parts:
        if expense_data.vendor:
            description_parts.append(f"Expense at {expense_data.vendor}")
        else:
            description_parts.append("Business expense")
    
    # Join and truncate to 64 characters
    description = " - ".join(description_parts)
    if len(description) > 64:
        description = description[:61] + "..."
    
    # Truncate vendor description to safe length (typically 64 chars)
    vendor_description = expense_data.vendor or "Unknown Vendor"
    if len(vendor_description) > 64:
        vendor_description = vendor_description[:61] + "..."
    
    return ExpenseEntryRequest(
        report_id=report_id,
        expense_type_code=expense_type_code,
        transaction_date=expense_data.transaction_date or datetime.now().strftime('%Y-%m-%d'),
        transaction_amount=expense_data.amount or 0.0,
        transaction_currency_code=expense_data.currency or "USD",
        payment_type_id=payment_type_id,
        description=description,
        vendor_description=vendor_description,
        # Use default location for now - could be enhanced to map cities
        location_id="D23A4483615E4A2084260E97E5F0D5E0",
        location_name="Miami, Florida",
        location_city="Miami",
        location_country_subdivision="US-FL",
        location_country="US"
    )

# Global variables for demo
current_expense_data: Optional[ExpenseData] = None
conversation_state: str = "initial"  # initial, waiting_for_choice, waiting_for_report_details, waiting_for_report_selection, waiting_for_tax_compliance
available_reports: List[Dict] = []
pending_report_data: Optional[Dict] = None  # Store report data while waiting for tax compliance
pending_expense_data: Optional[ExpenseData] = None  # Store expense data during report creation flow

def get_sap_headers():
    """Get SAP Concur API headers"""
    if not SAP_BEARER_TOKEN:
        raise HTTPException(status_code=500, detail="SAP Bearer token not configured")
    
    return {
        "Authorization": f"Bearer {SAP_BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

async def call_openai_vision(image_base64: str) -> Dict[str, Any]:
    """Extract expense data from receipt image using OpenAI Vision"""
    
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    prompt = """
    Analyze this receipt image and extract expense information. Return ONLY a JSON object with these exact fields:
    
    {
        "expense_type": "Choose from: Meals, Travel, Accommodation, Transportation, Office Supplies, Software, Entertainment, Fuel, Parking, Other",
        "transaction_date": "YYYY-MM-DD format",
        "business_purpose": "Infer likely business purpose based on vendor/items",
        "vendor": "Business/vendor name from receipt",
        "city": "City where transaction occurred",
        "country": "Country where transaction occurred",
        "payment_type": "Choose from: Credit Card, Cash, Bank Transfer, Check, Other",
        "amount": "Total amount as number (no currency symbols)",
        "currency": "Currency code like USD, EUR, etc.",
        "comment": "Additional details or itemized info from receipt"
    }
    
    Use null for any fields you cannot determine from the receipt. Be accurate with the amount.
    """
    
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        print(f"OpenAI Response: {content}")  # Debug log
        
        # Extract JSON from response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in OpenAI response")
            
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"OpenAI processing failed: {str(e)}")

async def get_sap_reports() -> List[Dict]:
    """Fetch all expense reports from SAP Concur"""
    try:
        url = f"{SAP_BASE_URL}/api/v3.0/expense/reports?limit=15&user={SAP_USER_LOGIN}"
        headers = get_sap_headers()
        
        print(f"Fetching reports from: {url}")  # Debug log
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"SAP Response Status: {response.status_code}")  # Debug log
        print(f"SAP Response: {response.text[:500]}...")  # Debug log
        
        response.raise_for_status()
        
        data = response.json()
        reports = data.get("Items", [])
        
        # Format reports for easier frontend consumption
        formatted_reports = []
        for report in reports:
            formatted_reports.append({
                "id": report.get("ID"),
                "name": report.get("Name"),
                "purpose": report.get("Purpose"),
                "total": report.get("Total"),
                "currency": report.get("CurrencyCode"),
                "status": report.get("ApprovalStatusName"),
                "created": report.get("CreateDate")
            })
        
        return formatted_reports
        
    except requests.exceptions.RequestException as e:
        print(f"SAP Reports Error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Failed to fetch SAP reports: {str(e)}")

async def create_sap_report(report_data: ReportCreateRequest) -> Dict:
    """Create new expense report in SAP Concur with tax compliance"""
    try:
        url = f"{SAP_BASE_URL}/expensereports/v4/users/{SAP_USER_ID}/context/TRAVELER/reports"
        headers = get_sap_headers()
        
        payload = {
            "customData": [
                {"id": "custom16", "value": str(report_data.gift_policy_compliance).lower()},
                {"id": "custom6", "value": str(report_data.irs_tax_policy_compliance).lower()}
            ],
            "businessPurpose": report_data.business_purpose,
            "comment": report_data.comment,
            "countryCode": report_data.country_code,
            "countrySubDivisionCode": report_data.country_subdivision_code,
            "name": report_data.name,
            "policyId": "2AFC92D1D0822F4A88D380BF14CFD05E"
        }
        
        print(f"Creating report at: {url}")  # Debug log
        print(f"Payload: {json.dumps(payload, indent=2)}")  # Debug log
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Create Report Response Status: {response.status_code}")  # Debug log
        print(f"Create Report Response Headers: {dict(response.headers)}")  # Debug log
        print(f"Create Report Response Text: {response.text}")  # Debug log
        
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json() if response.text else {}
        
        # SAP Concur v4 API might return the report ID in different ways
        # Let's also check the Location header for the created resource
        if 'Location' in response.headers:
            location = response.headers['Location']
            print(f"Location header: {location}")  # Debug log
            # Extract report ID from Location header if present
            # Location might be like: /expensereports/v4/users/{userId}/context/TRAVELER/reports/{reportId}
            if '/reports/' in location:
                report_id_from_location = location.split('/reports/')[-1]
                if not response_data.get('reportId'):
                    response_data['reportId'] = report_id_from_location
                    print(f"Extracted report ID from Location header: {report_id_from_location}")
        
        print(f"Final response data: {response_data}")  # Debug log
        return response_data
        
    except requests.exceptions.RequestException as e:
        print(f"SAP Create Report Error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Failed to create SAP report: {str(e)}")

def parse_report_details(message: str) -> Optional[Dict]:
    """Parse report details from user message with better flexibility"""
    
    # Try structured format first
    if ":" in message:
        lines = message.split('\n')
        report_name = ""
        business_purpose = ""
        comment = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if any(keyword in line.lower() for keyword in ["report name", "name"]) and ":" in line:
                report_name = line.split(':', 1)[1].strip()
            elif any(keyword in line.lower() for keyword in ["business purpose", "purpose"]) and ":" in line:
                business_purpose = line.split(':', 1)[1].strip()
            elif any(keyword in line.lower() for keyword in ["comment", "comments", "additional"]) and ":" in line:
                comment = line.split(':', 1)[1].strip()
        
        if report_name and business_purpose:
            return {
                "name": report_name,
                "business_purpose": business_purpose,
                "comment": comment or ""
            }
    
    # Try to extract from natural language
    message_lower = message.lower()
    
    # Look for common patterns
    name_patterns = [
        r"report.*?(?:name|called).*?[\"'](.*?)[\"']",
        r"name.*?[\"'](.*?)[\"']",
        r"call it [\"'](.*?)[\"']"
    ]
    
    purpose_patterns = [
        r"purpose.*?[\"'](.*?)[\"']",
        r"for [\"'](.*?)[\"']"
    ]
    
    extracted_name = ""
    extracted_purpose = ""
    
    for pattern in name_patterns:
        match = re.search(pattern, message_lower)
        if match:
            extracted_name = match.group(1)
            break
    
    for pattern in purpose_patterns:
        match = re.search(pattern, message_lower)
        if match:
            extracted_purpose = match.group(1)
            break
    
    if extracted_name and extracted_purpose:
        return {
            "name": extracted_name,
            "business_purpose": extracted_purpose,
            "comment": ""
        }
    
    return None

def parse_tax_compliance_response(message: str) -> Optional[Dict]:
    """Parse tax compliance checkbox responses from user message"""
    message_lower = message.lower()
    
    # Initialize default values
    gift_policy = False
    irs_tax_policy = False
    
    # Look for positive indicators for gift policy compliance
    if any(phrase in message_lower for phrase in [
        "gift policy: true", "gift policy: yes", "gift policy compliance: true", 
        "gift policy compliance: yes", "gift: true", "gift: yes",
        "custom16: true", "custom16: yes", "first: true", "first: yes",
        "✓ gift", "checked gift", "agree gift", "accept gift"
    ]):
        gift_policy = True
    
    # Look for positive indicators for IRS tax policy compliance
    if any(phrase in message_lower for phrase in [
        "irs tax policy: true", "irs tax policy: yes", "irs: true", "irs: yes",
        "tax policy: true", "tax policy: yes", "custom6: true", "custom6: yes",
        "second: true", "second: yes", "✓ irs", "checked irs", "agree irs", "accept irs"
    ]):
        irs_tax_policy = True
    
    # Look for structured format with both checkboxes
    lines = message.split('\n')
    for line in lines:
        line = line.strip().lower()
        if 'gift' in line and ('true' in line or 'yes' in line or '✓' in line):
            gift_policy = True
        if 'irs' in line and ('true' in line or 'yes' in line or '✓' in line):
            irs_tax_policy = True
    
    return {
        "gift_policy_compliance": gift_policy,
        "irs_tax_policy_compliance": irs_tax_policy
    }

# API Endpoints
@app.post("/api/process-receipt")
async def process_receipt(file: UploadFile = File(...)):
    """Process uploaded receipt and extract expense data"""
    global current_expense_data, conversation_state
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Extract expense data using OpenAI
        extracted_data = await call_openai_vision(image_base64)
        current_expense_data = ExpenseData(**extracted_data)
        conversation_state = "waiting_for_choice"
        
        return {
            "success": True,
            "message": "🎉 **Receipt processed successfully!**\n\nHere's what I extracted from your receipt:",
            "expense_data": current_expense_data.dict(),
            "next_action": "What would you like to do next?\n\n**1** - Create a new expense report\n**2** - Add to an existing report\n\nJust type **1** or **2** to continue!"
        }
        
    except Exception as e:
        print(f"Receipt processing error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Failed to process receipt: {str(e)}")

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """Handle chat messages and routing"""
    global current_expense_data, conversation_state, available_reports, pending_report_data, pending_expense_data
    
    user_message = message.content.strip()
    print(f"User message: {user_message}, State: {conversation_state}")  # Debug log
    
    try:
        # Handle different conversation states
        if conversation_state == "waiting_for_choice":
            if user_message in ["1", "new", "create new", "create"]:
                # Store current expense data before starting report creation flow
                pending_expense_data = current_expense_data
                conversation_state = "waiting_for_report_details"
                return {
                    "success": True,
                    "message": "Great! Let's create a new expense report.\n\nPlease provide the following information:\n\n**Report Name**: What should we call this report?\n**Business Purpose**: What's the purpose of this expense?\n\nYou can format it like this:\n```\nReport Name: July 2024 Office Supplies\nBusiness Purpose: Monthly office supplies purchase\n```\n\nOr just tell me in your own words!"
                }
            
            elif user_message in ["2", "existing", "add to existing"]:
                try:
                    reports = await get_sap_reports()
                    if not reports:
                        conversation_state = "waiting_for_choice"
                        return {
                            "success": True,
                            "message": "❌ No existing reports found. Would you like to create a new report instead?\n\nType **1** to create a new report."
                        }
                    
                    available_reports = reports
                    conversation_state = "waiting_for_report_selection"
                    
                    reports_text = "📋 **Here are your existing expense reports:**\n\n"
                    for i, report in enumerate(reports, 1):
                        status_emoji = "✅" if report['status'] == "Approved" else "⏳" if report['status'] == "Pending" else "📝"
                        reports_text += f"**{i}.** {status_emoji} **{report['name']}**\n"
                        reports_text += f"   • Purpose: {report['purpose'] or 'Not specified'}\n"
                        reports_text += f"   • Total: {report['total']} {report['currency']}\n"
                        reports_text += f"   • Status: {report['status']}\n\n"
                    
                    reports_text += "Please type the **number** of the report you'd like to add the expense to (e.g., type **3** for the third report)."
                    
                    return {
                        "success": True,
                        "message": reports_text
                    }
                    
                except Exception as e:
                    conversation_state = "waiting_for_choice"
                    return {
                        "success": False,
                        "message": f"❌ Failed to fetch reports: {str(e)}\n\nPlease try again or create a new report instead."
                    }
            
            else:
                return {
                    "success": False,
                    "message": "Please choose **1** for new report or **2** for existing report."
                }
        
        elif conversation_state == "waiting_for_report_details":
            # Try to parse report details
            report_details = parse_report_details(user_message)
            
            if report_details:
                # Store the report details and ask for tax compliance
                pending_report_data = report_details
                conversation_state = "waiting_for_tax_compliance"
                
                return {
                    "success": True,
                    "message": "Perfect! I have your report details:\n\n📊 **Report Information:**\n• **Name**: {}\n• **Purpose**: {}\n\n🏛️ **Tax & Policy Compliance Required**\n\nBefore creating your expense report, you must agree to the following policies as required by IRS and company regulations:\n\n**Please confirm your agreement by checking both boxes below:**\n\n☐ **Gift Policy Compliance Certification** - I certify that this expense complies with company gift policy guidelines\n☐ **IRS T&E Tax Policy Certification** - I certify that this expense complies with IRS Travel & Entertainment tax policies\n\n**To proceed, please respond with:**\n```\nGift Policy Compliance: ✓\nIRS Tax Policy Compliance: ✓\n```\n\nOr simply type **\"I agree to both policies\"** if you accept both certifications.".format(
                        report_details['name'], 
                        report_details['business_purpose']
                    ),
                    "needs_tax_compliance": True
                }
            else:
                return {
                    "success": False,
                    "message": "I couldn't understand the report details. Please provide:\n\n**Report Name**: What should we call this report?\n**Business Purpose**: What's the purpose?\n\nExample:\n```\nReport Name: July Office Supplies\nBusiness Purpose: Monthly office supplies\n```"
                }
        
        elif conversation_state == "waiting_for_tax_compliance":
            # Parse tax compliance response
            if any(phrase in user_message.lower() for phrase in [
                "i agree to both", "both policies", "agree to both", "accept both",
                "yes to both", "✓", "true", "agree", "accept", "yes"
            ]):
                # Check if we have pending report data
                if not pending_report_data:
                    return {
                        "success": False,
                        "message": "❌ Session expired. Please start over by creating a new report."
                    }
                
                # If user agrees to both or provides checkmarks, assume both are true
                compliance_data = parse_tax_compliance_response(user_message)
                
                # If user said "agree to both" or similar, set both to true
                if any(phrase in user_message.lower() for phrase in [
                    "i agree to both", "both policies", "agree to both", "accept both", "yes to both"
                ]):
                    compliance_data["gift_policy_compliance"] = True
                    compliance_data["irs_tax_policy_compliance"] = True
                
                # Check if at least one policy is agreed to
                if compliance_data and (compliance_data.get("gift_policy_compliance") or compliance_data.get("irs_tax_policy_compliance")):
                    try:
                        # Create the report with compliance data
                        report_request = ReportCreateRequest(
                            name=pending_report_data["name"],
                            business_purpose=pending_report_data["business_purpose"],
                            comment=pending_report_data.get("comment", ""),
                            gift_policy_compliance=compliance_data.get("gift_policy_compliance", False),
                            irs_tax_policy_compliance=compliance_data.get("irs_tax_policy_compliance", False)
                        )
                        
                        created_report = await create_sap_report(report_request)
                        
                        # Store the data before processing
                        report_name = pending_report_data["name"]
                        report_purpose = pending_report_data["business_purpose"]
                        
                        # Extract the report ID from the response - this is crucial!
                        report_id = None
                        if isinstance(created_report, dict):
                            # Try different possible response formats from SAP Concur
                            report_id = (created_report.get('reportId') or 
                                       created_report.get('ReportId') or 
                                       created_report.get('ID') or 
                                       created_report.get('Id'))
                        
                        print(f"Created report response: {created_report}")  # Debug log
                        print(f"Extracted report ID: {report_id}")  # Debug log
                        
                        # Try to add expense entry if we have both expense data and report ID
                        expense_added = False
                        expense_details = ""
                        expense_error = ""
                        
                        # Use pending_expense_data (preserved from the beginning) instead of current_expense_data
                        expense_data_to_use = pending_expense_data or current_expense_data
                        
                        if expense_data_to_use and report_id:
                            try:
                                print(f"Attempting to add expense to report ID: {report_id}")  # Debug log
                                
                                # Map expense data to entry format using the NEW report ID
                                expense_entry_data = map_expense_data_to_entry(expense_data_to_use, report_id)
                                
                                print(f"Mapped expense entry data: {expense_entry_data}")  # Debug log
                                
                                # Create the expense entry
                                created_entry = await create_expense_entry(expense_entry_data)
                                expense_added = True
                                
                                print(f"Successfully created expense entry: {created_entry}")  # Debug log
                                
                                expense_details = f"\n\n💰 **Expense Added:**\n• **Vendor**: {expense_entry_data.vendor_description}\n• **Amount**: ${expense_entry_data.transaction_amount:.2f} {expense_entry_data.transaction_currency_code}\n• **Date**: {expense_entry_data.transaction_date}\n• **Description**: {expense_entry_data.description}"
                                
                            except Exception as e:
                                print(f"Expense entry creation error during report creation: {str(e)}")  # Debug log
                                expense_error = str(e)
                                expense_details = f"\n\n⚠️ **Note**: Report created successfully, but there was an issue adding the expense entry: {str(e)}\nYou can manually add the expense in SAP Concur."
                        
                        elif not report_id:
                            print("No report ID found in response - cannot add expense")  # Debug log
                            expense_details = f"\n\n⚠️ **Note**: Report created successfully, but could not extract report ID to add expense entry.\nYou can manually add the expense in SAP Concur."
                        
                        elif not expense_data_to_use:
                            print("No expense data available - skipping expense entry creation")  # Debug log
                        
                        # Clear state
                        conversation_state = "initial"
                        current_expense_data = None
                        pending_report_data = None
                        pending_expense_data = None  # Clear the pending expense data
                        
                        compliance_status = []
                        if compliance_data.get("gift_policy_compliance"):
                            compliance_status.append("✅ Gift Policy Compliance")
                        else:
                            compliance_status.append("❌ Gift Policy Compliance")
                        
                        if compliance_data.get("irs_tax_policy_compliance"):
                            compliance_status.append("✅ IRS T&E Tax Policy Compliance")
                        else:
                            compliance_status.append("❌ IRS T&E Tax Policy Compliance")
                        
                        success_message = f"✅ **Report created successfully!**\n\n📊 **Report Details:**\n• **Name**: {report_name}\n• **Purpose**: {report_purpose}\n• **Report ID**: {report_id or 'N/A'}\n\n🏛️ **Policy Compliance Status:**\n{chr(10).join(compliance_status)}{expense_details}\n\n🎉 {'Your expense report is complete with the expense entry!' if expense_added else 'Your expense report is ready for expenses!'}"
                        
                        return {
                            "success": True,
                            "message": success_message
                        }
                        
                    except Exception as e:
                        print(f"Report creation error: {str(e)}")  # Debug log
                        # Clear state on error
                        conversation_state = "initial"
                        current_expense_data = None
                        pending_report_data = None
                        pending_expense_data = None
                        return {
                            "success": False,
                            "message": f"❌ Failed to create report: {str(e)}\n\nPlease try again with the compliance confirmations."
                        }
                else:
                    return {
                        "success": False,
                        "message": "⚠️ **Policy Compliance Required**\n\nYou must agree to at least one of the policy certifications to create an expense report. Please confirm:\n\n☐ **Gift Policy Compliance Certification**\n☐ **IRS T&E Tax Policy Certification**\n\nType **\"I agree to both policies\"** or confirm each policy individually."
                    }
            else:
                return {
                    "success": False,
                    "message": "🏛️ **Policy Compliance Required**\n\nPlease confirm your agreement to the required policies:\n\n☐ **Gift Policy Compliance Certification**\n☐ **IRS T&E Tax Policy Certification**\n\nRespond with:\n```\nGift Policy Compliance: ✓\nIRS Tax Policy Compliance: ✓\n```\n\nOr type **\"I agree to both policies\"** to accept both."
                }
        
        elif conversation_state == "waiting_for_report_selection":
            try:
                selection = int(user_message)
                if 1 <= selection <= len(available_reports):
                    selected_report = available_reports[selection - 1]
                    
                    # Create expense entry for the selected report
                    if current_expense_data:
                        try:
                            # Map expense data to entry format
                            expense_entry_data = map_expense_data_to_entry(current_expense_data, selected_report['id'])
                            
                            # Create the expense entry
                            created_entry = await create_expense_entry(expense_entry_data)
                            
                            conversation_state = "initial"
                            current_expense_data = None
                            
                            return {
                                "success": True,
                                "message": f"✅ **Expense added successfully!**\n\n📊 **Report Details:**\n• **Report**: {selected_report['name']}\n• **Previous Total**: {selected_report['total']} {selected_report['currency']}\n• **New Expense**: ${expense_entry_data.transaction_amount:.2f}\n• **Status**: {selected_report['status']}\n\n💰 **Expense Details:**\n• **Vendor**: {expense_entry_data.vendor_description}\n• **Amount**: ${expense_entry_data.transaction_amount:.2f} {expense_entry_data.transaction_currency_code}\n• **Date**: {expense_entry_data.transaction_date}\n• **Description**: {expense_entry_data.description}\n\n🎉 Your expense has been successfully added to the report!"
                            }
                            
                        except Exception as e:
                            print(f"Expense entry creation error: {str(e)}")  # Debug log
                            conversation_state = "initial"
                            current_expense_data = None
                            
                            return {
                                "success": False,
                                "message": f"✅ **Report selected successfully!**\n\n📊 **Selected Report:**\n• Name: {selected_report['name']}\n• Purpose: {selected_report['purpose']}\n• Current Total: {selected_report['total']} {selected_report['currency']}\n• Status: {selected_report['status']}\n\n❌ **Note**: There was an issue adding the expense entry to SAP Concur: {str(e)}\n\nThe report selection was successful, but you may need to manually add the expense details in SAP Concur."
                            }
                    else:
                        conversation_state = "initial"
                        return {
                            "success": True,
                            "message": f"✅ **Report selected!**\n\n📊 **Selected Report:**\n• Name: {selected_report['name']}\n• Purpose: {selected_report['purpose']}\n• Current Total: {selected_report['total']} {selected_report['currency']}\n• Status: {selected_report['status']}\n\n🎉 Your report is ready for expenses!"
                        }
                else:
                    return {
                        "success": False,
                        "message": f"❌ Invalid selection. Please choose a number between 1 and {len(available_reports)}."
                    }
                    
            except ValueError:
                return {
                    "success": False,
                    "message": "❌ Please enter a valid number to select a report."
                }
        
        else:  # initial state
            # Check for report fetching commands
            if any(phrase in user_message.lower() for phrase in [
                "show reports", "list reports", "get reports", "fetch reports", 
                "view reports", "my reports", "existing reports", "all reports",
                "show my reports", "list my reports"
            ]):
                try:
                    reports = await get_sap_reports()
                    if not reports:
                        return {
                            "success": True,
                            "message": "📋 **No Reports Found**\n\nYou don't have any expense reports yet. Would you like to create one by uploading a receipt?"
                        }
                    
                    reports_text = f"📋 **Your Expense Reports** ({len(reports)} found)\n\n"
                    
                    for i, report in enumerate(reports, 1):
                        # Status emoji mapping
                        status_emoji = {
                            "Approved": "✅",
                            "Submitted": "📤", 
                            "Pending Approval": "⏳",
                            "Draft": "📝",
                            "Rejected": "❌"
                        }.get(report['status'], "📄")
                        
                        # Format created date
                        created_date = "Unknown"
                        if report.get('created'):
                            try:
                                created_date = datetime.fromisoformat(report['created'].replace('T', ' ').replace('Z', '')).strftime('%m/%d/%Y')
                            except:
                                created_date = report['created'][:10] if len(report['created']) >= 10 else "Unknown"
                        
                        reports_text += f"**{i}.** {status_emoji} **{report['name']}**\n"
                        reports_text += f"   • Purpose: {report['purpose'] or 'Not specified'}\n"
                        reports_text += f"   • Amount: {report['total']} {report['currency']}\n"
                        reports_text += f"   • Status: {report['status']}\n"
                        reports_text += f"   • Created: {created_date}\n"
                        reports_text += f"   • ID: {report['id']}\n\n"
                    
                    reports_text += "💡 **Want to add an expense?** Upload a receipt and I'll help you add it to one of these reports!"
                    
                    return {
                        "success": True,
                        "message": reports_text,
                        "reports": reports
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"❌ **Failed to fetch reports**\n\nError: {str(e)}\n\nPlease check your SAP Concur connection and try again."
                    }
            
            # Check for help commands
            elif any(phrase in user_message.lower() for phrase in [
                "help", "what can you do", "commands", "options"
            ]):
                return {
                    "success": True,
                    "message": "🤖 **Here's what I can help you with:**\n\n📷 **Upload Receipt**: Drag & drop or click 📎 to upload a receipt image\n📋 **View Reports**: Type 'show my reports' to see all your expense reports\n➕ **Create Report**: Upload a receipt and I'll help you create a new report\n🔗 **Add to Existing**: Upload a receipt and add it to an existing report\n\n💡 **Quick Commands:**\n• `show reports` - View all your reports\n• `help` - Show this help message\n\nJust upload a receipt to get started!"
                }
            
            # Default responses based on current state
            elif current_expense_data:
                conversation_state = "waiting_for_choice"
                return {
                    "success": True,
                    "message": "I have your expense data ready! What would you like to do?\n\n**1** - Create a new expense report\n**2** - Add to an existing report\n\nType **1** or **2** to continue!",
                    "expense_data": current_expense_data.dict()
                }
            else:
                return {
                    "success": True,
                    "message": "👋 **Welcome to the Expense Assistant!**\n\nI'm here to help you streamline your expense reporting process. Here's what I can do for you:\n\n• **📷 Upload receipts** - Just drag & drop or click the attachment button, and I'll automatically extract all the expense details\n• **📋 Manage reports** - Type 'show reports' to view your existing expense reports\n• **💬 Get help** - Type 'help' to see all available commands\n\nReady to get started? Upload a receipt or ask me anything!"
                }
    
    except Exception as e:
        print(f"Chat error: {str(e)}")  # Debug log
        # Clear all state on error
        conversation_state = "initial"
        current_expense_data = None
        pending_report_data = None
        pending_expense_data = None
        return {
            "success": False,
            "message": f"❌ Something went wrong: {str(e)}\n\nPlease try again or upload a new receipt to start over."
        }

@app.get("/api/reports")
async def get_reports():
    """Get all expense reports"""
    try:
        reports = await get_sap_reports()
        return {
            "success": True,
            "reports": reports,
            "count": len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/formatted")
async def get_reports_formatted():
    """Get all expense reports with formatted message for chat"""
    try:
        reports = await get_sap_reports()
        if not reports:
            return {
                "success": True,
                "message": "📋 **No Reports Found**\n\nYou don't have any expense reports yet. Would you like to create one by uploading a receipt?",
                "reports": [],
                "count": 0
            }
        
        reports_text = f"📋 **Your Expense Reports** ({len(reports)} found)\n\n"
        
        for i, report in enumerate(reports, 1):
            # Status emoji mapping
            status_emoji = {
                "Approved": "✅",
                "Submitted": "📤", 
                "Pending Approval": "⏳",
                "Draft": "📝",
                "Rejected": "❌"
            }.get(report['status'], "📄")
            
            # Format created date
            created_date = "Unknown"
            if report.get('created'):
                try:
                    created_date = datetime.fromisoformat(report['created'].replace('T', ' ').replace('Z', '')).strftime('%m/%d/%Y')
                except:
                    created_date = report['created'][:10] if len(report['created']) >= 10 else "Unknown"
            
            reports_text += f"**{i}.** {status_emoji} **{report['name']}**\n"
            reports_text += f"   • Purpose: {report['purpose'] or 'Not specified'}\n"
            reports_text += f"   • Amount: {report['total']} {report['currency']}\n"
            reports_text += f"   • Status: {report['status']}\n"
            reports_text += f"   • Created: {created_date}\n"
            reports_text += f"   • ID: {report['id']}\n\n"
        
        reports_text += "💡 **Want to add an expense?** Upload a receipt and I'll help you add it to one of these reports!"
        
        return {
            "success": True,
            "message": reports_text,
            "reports": reports,
            "count": len(reports)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@app.post("/api/reports")
async def create_report(report_data: ReportCreateRequest):
    """Create new expense report"""
    try:
        created_report = await create_sap_report(report_data)
        return {
            "success": True,
            "message": "Report created successfully!",
            "report": created_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expense-entry")
async def create_expense_entry_endpoint(expense_data: ExpenseEntryRequest):
    """Create new expense entry"""
    try:
        created_entry = await create_expense_entry(expense_data)
        return {
            "success": True,
            "message": "Expense entry created successfully!",
            "entry": created_entry
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-expense-to-report")
async def add_expense_to_report(report_id: str, expense_data: ExpenseData):
    """Add expense data to existing report"""
    try:
        # Map expense data to entry format
        expense_entry_data = map_expense_data_to_entry(expense_data, report_id)
        
        # Create the expense entry
        created_entry = await create_expense_entry(expense_entry_data)
        
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

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "openai_configured": bool(openai.api_key),
            "sap_configured": bool(SAP_BEARER_TOKEN)
        }
    }

@app.get("/")
async def root():
    return {
        "message": "Simplified Expense Processing API",
        "version": "1.0.0",
        "status": "ready",
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