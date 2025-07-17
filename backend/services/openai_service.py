import openai
import base64
import json
from typing import Dict, Any
from fastapi import HTTPException
from config.settings import settings

class OpenAIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def extract_expense_data(self, image_base64: str) -> Dict[str, Any]:
        """Extract expense data from receipt image using OpenAI Vision"""
        
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
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in OpenAI response")
                
        except Exception as e:
            print(f"OpenAI Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI processing failed: {str(e)}")