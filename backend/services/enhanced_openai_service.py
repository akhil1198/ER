import openai
import base64
import json
from typing import Dict, Any
from fastapi import HTTPException
from config.settings import settings

class EnhancedOpenAIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def extract_expense_data(self, image_base64: str) -> Dict[str, Any]:
        """Extract comprehensive expense data from receipt image for SAP Concur"""
        
        prompt = """
        Analyze this receipt image and extract expense information. Return ONLY a JSON object with these exact fields:
        
        {
            "expense_category": "Determine the main category from: Meals & Entertainment, Lodging, Transportation, Office Supplies, Travel, Other",
            "expense_type": "For Meals & Entertainment, choose from: Meals Employee(s) Only - In Town, Meals Employee(s) Only - Out of Town, Meals with Carrier(s), Meals with Client Prospect(s), Meals with Client(s) - In Town, Meals with Client(s) - Out of Town, Meals with M&A Prospect(s). For other categories, use generic types like Hotel, Airfare, Gas, etc.",
            "meal_type": "If this is a meal, specify: Breakfast, Lunch, Dinner, or Other. If not a meal, set to null",
            "transaction_date": "YYYY-MM-DD format from the receipt",
            "business_purpose": "Infer the business purpose. For meals, consider if it's with clients, employees, prospects, etc. Examples: 'Team dinner for project discussion', 'Client lunch meeting', 'Employee breakfast meeting'",
            "vendor": "Business/vendor name from receipt (this will be the vendor field)",
            "city": "City where transaction occurred",
            "country": "Country where transaction occurred (use country codes like US, CA, UK)",
            "payment_type": "Choose from: Cash, Personal Credit Card, Corporate Credit Card, Bank Transfer, Check",
            "amount": "Total amount as number (no currency symbols)",
            "currency": "Currency code like USD, EUR, etc.",
            "attendees_count": "Number of people who attended (for meals). If not applicable, set to 1",
            "client_prospect_name": "If this is a client/prospect meal, extract or infer the company/person name. Otherwise null",
            "comment": "Additional details, itemized info, or special notes from receipt"
        }
        
        Important rules:
        1. For Meals & Entertainment, be specific about the expense type based on context clues
        2. If receipt shows multiple people or mentions client/team, choose appropriate meal type
        3. Extract vendor name accurately as it will populate the Vendor field
        4. Business purpose should be professional and descriptive
        5. Use null for fields that don't apply to this expense type
        6. If the receipt uploaded is an Uber receipt, the type should be "Transportation" and the expense type should be "Taxi/Rideshare". The vendor should be "Uber" or "Lyft" based on the receipt.
        """
        
        try:
            response = self.client.chat.completions.create(
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
            print(f"OpenAI Response: {content}")
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                extracted_data = json.loads(json_str)
                
                # Post-process and validate the data
                return self._validate_and_enhance_data(extracted_data)
            else:
                raise ValueError("No valid JSON found in OpenAI response")
                
        except Exception as e:
            print(f"OpenAI Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI processing failed: {str(e)}")
    
    def _validate_and_enhance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance extracted data"""
        
        # Validate expense category
        valid_categories = [
            "Meals & Entertainment", "Lodging", "Transportation", 
            "Office Supplies", "Travel", "Other"
        ]
        if data.get("expense_category") not in valid_categories:
            data["expense_category"] = "Other"
        
        # Validate Meals & Entertainment expense types
        meals_entertainment_types = [
            "Meals Employee(s) Only - In Town",
            "Meals Employee(s) Only - Out of Town", 
            "Meals with Carrier(s)",
            "Meals with Client Prospect(s)",
            "Meals with Client(s) - In Town",
            "Meals with Client(s) - Out of Town",
            "Meals with M&A Prospect(s)"
        ]
        
        if data.get("expense_category") == "Meals & Entertainment":
            if data.get("expense_type") not in meals_entertainment_types:
                # Default to employee meal if not specified
                data["expense_type"] = "Meals Employee(s) Only - In Town"
        
        # Validate meal types
        valid_meal_types = ["Breakfast", "Lunch", "Dinner", "Other"]
        if data.get("meal_type") and data.get("meal_type") not in valid_meal_types:
            data["meal_type"] = "Other"
        
        # Validate payment types
        valid_payment_types = [
            "Cash", "Personal Credit Card", "Corporate Credit Card", 
            "Bank Transfer", "Check"
        ]
        if data.get("payment_type") not in valid_payment_types:
            data["payment_type"] = "Personal Credit Card"
        
        # Ensure attendees count is at least 1
        if not data.get("attendees_count") or data.get("attendees_count") < 1:
            data["attendees_count"] = 1
        
        # Ensure amount is a valid number
        try:
            data["amount"] = float(data.get("amount", 0))
        except (ValueError, TypeError):
            data["amount"] = 0.0
        
        return data