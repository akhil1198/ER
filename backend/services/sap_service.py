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
    
    async def create_expense_entry(self, expense_data: ExpenseEntryRequest) -> Dict:
        """Create new expense entry in SAP Concur"""
        try:
            url = f"{settings.SAP_BASE_URL}/api/v3.0/expense/entries?user={settings.SAP_USER_LOGIN}"
            headers = self._get_headers()
            
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
            
            print(f"Creating expense entry at: {url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"Description length: {len(description)}")
            print(f"Vendor description length: {len(vendor_description)}")
            
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
            print(f"SAP Create Expense Entry Error: {str(e)}")
            error_detail = f"Failed to create expense entry: {str(e)}"
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'Message' in error_data:
                        error_detail = f"SAP Concur error: {error_data['Message']}"
                except:
                    pass
                    
            raise HTTPException(status_code=500, detail=error_detail)