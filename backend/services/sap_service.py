import requests
import json
from typing import Dict, List
from fastapi import HTTPException
from config.settings import settings
from models.report import ReportCreateRequest
from models.expense import ExpenseEntryRequest

class SAPService:
    def __init__(self):
        if not settings.SAP_BEARER_TOKEN:
            raise ValueError("SAP Bearer token not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get SAP Concur API headers"""
        return {
            "Authorization": f"Bearer {settings.SAP_BEARER_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_reports(self) -> List[Dict]:
        """Fetch all expense reports from SAP Concur"""
        try:
            url = f"{settings.SAP_BASE_URL}/api/v3.0/expense/reports?limit=15&user={settings.SAP_USER_LOGIN}"
            headers = self._get_headers()
            
            print(f"Fetching reports from: {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            print(f"SAP Response Status: {response.status_code}")
            print(f"SAP Response: {response.text[:500]}...")
            
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
            print(f"SAP Reports Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch SAP reports: {str(e)}")
    
    async def create_report(self, report_data: ReportCreateRequest) -> Dict:
        """Create new expense report in SAP Concur with tax compliance"""
        try:
            url = f"{settings.SAP_BASE_URL}/expensereports/v4/users/{settings.SAP_USER_ID}/context/TRAVELER/reports"
            headers = self._get_headers()
            
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
                "policyId": settings.DEFAULT_POLICY_ID
            }
            
            print(f"Creating report at: {url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"Create Report Response Status: {response.status_code}")
            print(f"Create Report Response Headers: {dict(response.headers)}")
            print(f"Create Report Response Text: {response.text}")
            
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json() if response.text else {}
            
            # SAP Concur v4 API might return the report ID in different ways
            if 'Location' in response.headers:
                location = response.headers['Location']
                print(f"Location header: {location}")
                if '/reports/' in location:
                    report_id_from_location = location.split('/reports/')[-1]
                    if not response_data.get('reportId'):
                        response_data['reportId'] = report_id_from_location
                        print(f"Extracted report ID from Location header: {report_id_from_location}")
            
            print(f"Final response data: {response_data}")
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f"SAP Create Report Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create SAP report: {str(e)}")
    
    async def create_expense_entry_enhanced(self, expense_data: Dict[str, any]) -> Dict:
        """Create new expense entry in SAP Concur with enhanced data mapping"""
        try:
            url = f"{settings.SAP_BASE_URL}/api/v3.0/expense/entries?user={settings.SAP_USER_LOGIN}"
            headers = self._get_headers()
            
            # Build the payload from the enhanced expense data
            payload = {
                "ReportID": expense_data["ReportID"],
                "ExpenseTypeCode": expense_data["ExpenseTypeCode"],
                "TransactionDate": expense_data["TransactionDate"],
                "TransactionAmount": expense_data["TransactionAmount"],
                "TransactionCurrencyCode": expense_data["TransactionCurrencyCode"],
                "PaymentTypeID": expense_data["PaymentTypeID"],
                "Description": expense_data["Description"],
                "VendorDescription": expense_data["VendorDescription"],
                "Location": expense_data["Location"],
                "IsPersonal": expense_data.get("IsPersonal", False),
                "IsBillable": expense_data.get("IsBillable", False),
                "TaxReceiptType": expense_data.get("TaxReceiptType", "R")
            }
            
            # Add custom fields if they exist
            custom_fields = []
            for i in range(1, 5):  # Custom1 through Custom4
                custom_key = f"Custom{i}"
                if custom_key in expense_data and expense_data[custom_key]:
                    custom_fields.append({
                        "Name": custom_key,
                        "Value": str(expense_data[custom_key])
                    })
            
            if custom_fields:
                payload["CustomFields"] = custom_fields
            
            if "Custom1" in expense_data and expense_data["Custom1"]:
                payload["Custom1"] = str(expense_data["Custom1"])
            if "Custom2" in expense_data and expense_data["Custom2"]:
                payload["Custom2"] = str(expense_data["Custom2"])
            if "Custom3" in expense_data and expense_data["Custom3"]:
                payload["Custom3"] = str(expense_data["Custom3"])
            if "Custom4" in expense_data and expense_data["Custom4"]:
                payload["Custom4"] = str(expense_data["Custom4"])

            print(f"🚀 SAP Payload: {json.dumps(payload, indent=2)}")
            
            print(f"Creating enhanced expense entry at: {url}")
            print(f"Enhanced Payload: {json.dumps(payload, indent=2)}")
            print(f"Description length: {len(payload['Description'])}")
            print(f"Vendor description length: {len(payload['VendorDescription'])}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"Create Enhanced Expense Response Status: {response.status_code}")
            print(f"Create Enhanced Expense Response: {response.text}")
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('Message', 'Bad Request')
                    print(f"SAP API Error: {error_message}")
                    
                    # Log the full error details for debugging
                    if 'Details' in error_data:
                        print(f"SAP API Error Details: {error_data['Details']}")
                    
                    raise HTTPException(status_code=400, detail=f"SAP Concur API error: {error_message}")
                except (json.JSONDecodeError, KeyError):
                    raise HTTPException(status_code=400, detail=f"SAP Concur API error: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"SAP Create Enhanced Expense Entry Error: {str(e)}")
            error_detail = f"Failed to create expense entry: {str(e)}"
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'Message' in error_data:
                        error_detail = f"SAP Concur error: {error_data['Message']}"
                    if 'Details' in error_data:
                        error_detail += f" - Details: {error_data['Details']}"
                except:
                    pass
                    
            raise HTTPException(status_code=500, detail=error_detail)
    
    async def create_expense_entry(self, expense_data: ExpenseEntryRequest) -> Dict:
        """Create new expense entry in SAP Concur"""


        try:
            url = f"{settings.SAP_BASE_URL}/api/v3.0/expense/entries?user={settings.SAP_USER_LOGIN}"
            headers = self._get_headers()
            
            print("------------ Creating expense entry in SAP Concur with this expense data ------------->", expense_data)
            print("report_id:", expense_data.get("ReportID"))
            print("expense_type_code:", expense_data.get("ExpenseTypeCode"))
            print("transaction_date:", expense_data.get("TransactionDate"))
            print("TransactionAmount:", expense_data.get("amount"))
            print("description:", expense_data.get("description"))
            print("vendor:", expense_data.get("vendor"))
            # Validate and sanitize data before sending
            description = expense_data.get("description", "")[:64] if expense_data.get("description") else "Business expense"
            vendor_description = expense_data.get("vendor", "")[:64] if expense_data.get("vendor") else "Vendor"

            if expense_data.get("ExpenseTypeCode") == "01072": # rideshare
                payload = {
                    'ReportID': expense_data.get("ReportID"), 
                    'ExpenseTypeCode': expense_data.get("ExpenseTypeCode"), 
                    'TransactionDate': expense_data.get("TransactionDate"), 
                    'description': expense_data.get("description"), 
                    'FromLocation': "chicago", 
                    'paymentTypeId': "gWuT0oX4FNnukaeUcpOO3WSub$p5tY", 
                    'TransactionAmount': expense_data.get("TransactionAmount"), 
                    'TransactionCurrencyCode': expense_data.get("TransactionCurrencyCode"), 
                    'VendorDescription': expense_data.get("VendorDescription"), 
                    'comment': expense_data.get("comment"), 
                    'custom9': "client" # custom9 is for client/prospect name
                }
            elif expense_data.get("ExpenseTypeCode") == "01028": # meal
                payload = {
                    'ReportID': expense_data.get("ReportID"), 
                    'ExpenseTypeCode': expense_data.get("ExpenseTypeCode"), 
                    'TransactionDate': expense_data.get("TransactionDate"), 
                    'TransactionAmount': expense_data.get("TransactionAmount"), 
                    'TransactionCurrencyCode': expense_data.get("TransactionCurrencyCode"), 
                    'paymentTypeId': "gWuT0oX4FNnukaeUcpOO3WSub$p5tY", 
                    'description': expense_data.get("description"), 
                    'VendorDescription': expense_data.get("VendorDescription"), 
                    'comment': expense_data.get("comment"), 
                    'expense_type': expense_data.get("expense_type"),
                    'custom9': "ap" # custom9 is for client/prospect name
                }

            print(f"Creating expense entry at: {url}")
            print(f"Payload: {payload}")
            # print(f"Description length: {len(description)}")
            # print(f"Vendor description length: {len(vendor_description)}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"Create Expense Response Status: {response.status_code}")
            print(f"Create Expense Response: {response.text}")
            
            if response.status_code == 400:
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
            print(f"SAP Create Legacy Expense Entry Error: {str(e)}")
            error_detail = f"Failed to create expense entry: {str(e)}"
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'Message' in error_data:
                        error_detail = f"SAP Concur error: {error_data['Message']}"
                except:
                    pass
                    
            raise HTTPException(status_code=500, detail=error_detail)

    def _log_api_call(self, method: str, url: str, payload: Dict = None, response_status: int = None, response_text: str = None):
        """Helper method to log API calls for debugging"""
        print(f"\n{'='*50}")
        print(f"SAP CONCUR API CALL")
        print(f"{'='*50}")
        print(f"Method: {method}")
        print(f"URL: {url}")
        if payload:
            print(f"Payload: {json.dumps(payload, indent=2)}")
        if response_status:
            print(f"Response Status: {response_status}")
        if response_text:
            print(f"Response: {response_text[:1000]}...")
        print(f"{'='*50}\n")