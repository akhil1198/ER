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
        """Extract comprehensive expense data from receipt image with intelligent categorization"""
        
        prompt = """
        Analyze this receipt image and extract expense information using this intelligent 3-step process:

        STEP 1: CATEGORY DETECTION
        First, determine the main expense category by examining the receipt:
        - "Transportation" - For Uber, Lyft, taxi, rideshare, car rental, gas, parking, flights, trains
        - "Meals & Entertainment" - For restaurants, food, cafes, bars, catering, meals

        STEP 2: EXPENSE TYPE DETECTION
        Based on the category detected, choose the most specific expense type:

        If Transportation:
        - "Rideshare (Uber, Lyft)" - For Uber, Lyft, rideshare services
        - "Taxi/Limo" - For traditional taxis and limo services
        - "Car Rental" - For car rental companies
        - "Parking/Tolls" - For parking fees, toll charges
        - "Airfare-Employee" - For flight tickets
        - "Gas - Leased Car" - For gas stations when using company/leased vehicle

        If Meals & Entertainment:
        - "Meals Employee(s) Only - In Town" - For meals with only company employees, no clients
        - "Meals with Client(s) - In Town" - For business meals with clients/prospects
        - "Meals with Client(s) - Out of Town" - For business meals with clients while traveling
        - "Meeting/Catering" - For catering services, meeting refreshments

        STEP 3: DYNAMIC FIELD MAPPING
        Based on the detected expense type, extract data into the appropriate field structure:

        For "Rideshare (Uber, Lyft)":
        {
            "category": "Transportation",
            "expense_type": "Rideshare (Uber, Lyft)",
            "transaction_date": "YYYY-MM-DD format",
            "business_purpose": "Business purpose (e.g., 'Client meeting transportation', 'Airport transfer')",
            "travel_type": "Domestic or International",
            "starting_city": "City where trip started",
            "country": "Country code (US, CA, UK, etc.)",
            "payment_type": "Cash, Personal Credit Card",
            "amount": "Total amount as number",
            "currency": "Currency code (USD, EUR, etc.)",
            "vendor": "Uber, Lyft, or rideshare company name",
            "comment": "Trip details, destination, or additional notes"
        }

        For "Meals with Client(s) - In Town":
        {
            "category": "Meals & Entertainment",
            "expense_type": "Meals with Client(s) - In Town",
            "transaction_date": "YYYY-MM-DD format",
            "business_purpose": "Business purpose (e.g., 'Client lunch meeting', 'Prospect dinner discussion')",
            "meal_type": "Breakfast, Lunch, Dinner, or Other",
            "vendor": "Restaurant/vendor name",
            "city": "City where meal occurred",
            "country": "Country code (US, CA, UK, etc.)",
            "payment_type": "Cash, Personal Credit Card",
            "amount": "Total amount as number",
            "currency": "Currency code (USD, EUR, etc.)",
            "attendees_count": "Number of people who attended (minimum 2 for client meals)",
            "client_prospect_name": "Name of client company or prospect",
            "comment": "Additional details about the meal or attendees"
        }

        For "Meals Employee(s) Only - In Town":
        {
            "category": "Meals & Entertainment", 
            "expense_type": "Meals Employee(s) Only - In Town",
            "transaction_date": "YYYY-MM-DD format",
            "business_purpose": "Business purpose (e.g., 'Team working lunch', 'Employee meeting meal')",
            "meal_type": "Breakfast, Lunch, Dinner, or Other",
            "vendor": "Restaurant/vendor name",
            "city": "City where meal occurred", 
            "country": "Country code (US, CA, UK, etc.)",
            "payment_type": "Cash, Personal Credit Card",
            "amount": "Total amount as number",
            "currency": "Currency code (USD, EUR, etc.)",
            "attendees_count": "Number of employees who attended",
            "comment": "Additional details about the meal"
        }

        DETECTION LOGIC:
        1. Look for company logos (Uber, Lyft = Rideshare; restaurant names = Meals)
        2. Analyze receipt format (rideshare apps have trip details; restaurants have food items)
        3. Check for meal indicators (food items, menu items, dining time)
        4. Check for transport indicators (pickup/dropoff locations, trip duration, vehicle info)
        5. For meals, determine if clients are involved based on:
        - High per-person cost (suggests client meal)
        - Business location/upscale restaurant
        - Multiple attendees mentioned
        - Business-related notes or context

        IMPORTANT RULES:
        1. Be very accurate with category detection - this determines the entire form structure
        2. Choose the most specific expense type that matches the receipt
        3. Extract vendor name exactly as it appears on the receipt
        4. For rideshare: Include trip details in business_purpose and comment
        5. For meals: Infer attendee count from total amount (if unusually high for one person, likely multiple attendees)
        6. Use context clues to determine if meal involves clients vs employees only
        7. Set travel_type as "Domestic" for US trips, "International" for cross-border
        8. Use null for fields that don't apply or can't be determined

        Return ONLY a valid JSON object with the appropriate field structure based on the detected expense type.
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
                max_tokens=1500,  # Increased for more detailed analysis
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
        """Validate and enhance extracted data with improved logic"""
        
        # Validate category
        valid_categories = ["Transportation", "Meals & Entertainment"]
        if data.get("category") not in valid_categories:
            # Try to infer from expense_type
            expense_type = data.get("expense_type", "").lower()
            if any(word in expense_type for word in ["uber", "lyft", "taxi", "rideshare", "car", "parking", "gas"]):
                data["category"] = "Transportation"
            elif any(word in expense_type for word in ["meal", "restaurant", "food", "catering"]):
                data["category"] = "Meals & Entertainment"
            else:
                data["category"] = "nOne"  # Default fallback
        
        # Validate expense types based on category
        transportation_types = [
            "Rideshare (Uber, Lyft)", 
            "Taxi/Limo", 
            "Car Rental", 
            "Car Rental Gas", 
            "Parking/Tolls", 
            "Monthly Parking",
            "Other Ground Trans. (Shuttle, Bus, Ferry, Subway)",
            "Gas - Leased Car",
            "Car Mileage"
        ]
        meals_types = [
            "Meals Employee(s) Only - In Town", 
            "Meals with Client(s) - In Town",
            "Meals with Client(s) - Out of Town", 
            "Meeting/Catering"
        ]
        
        if data.get("category") == "Transportation":
            if data.get("expense_type") not in transportation_types:
                # Auto-detect based on vendor
                vendor = data.get("vendor", "").lower()
                if "uber" in vendor or "lyft" in vendor:
                    data["expense_type"] = "Rideshare (Uber, Lyft)"
                else:
                    data["expense_type"] = "Taxi/Limo"  # Default for transportation
        
        elif data.get("category") == "Meals & Entertainment":
            if data.get("expense_type") not in meals_types:
                # Auto-detect based on context
                attendees = data.get("attendees_count", 1)
                client_name = data.get("client_prospect_name")
                if client_name or attendees > 2:
                    data["expense_type"] = "Meals with Client(s) - In Town"
                else:
                    data["expense_type"] = "Meals Employee(s) Only - In Town"
        
        # Validate and set defaults for common fields
        if not data.get("payment_type"):
            data["payment_type"] = "Cash"
        
        if not data.get("currency"):
            data["currency"] = "USD"
        
        if not data.get("country"):
            data["country"] = "US"
        
        # Ensure amount is a valid number
        try:
            data["amount"] = float(data.get("amount", 0))
        except (ValueError, TypeError):
            data["amount"] = 0.0
        
        # Set travel_type default for transportation
        if data.get("category") == "Transportation" and not data.get("travel_type"):
            data["travel_type"] = "Domestic"
        
        # Ensure attendees_count is at least 1
        if data.get("attendees_count"):
            try:
                data["attendees_count"] = max(1, int(data.get("attendees_count", 1)))
            except (ValueError, TypeError):
                data["attendees_count"] = 1
        
        return data