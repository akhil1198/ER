from datetime import datetime
from typing import Dict
from models.expense import EnhancedExpenseData, EnhancedExpenseEntryRequest
from config.settings import settings

class EnhancedExpenseService:
    
    # Comprehensive expense type mapping for SAP Concur
    EXPENSE_TYPE_MAPPING = {
        # Meals & Entertainment
        "meals employee(s) only - in town": "01028",
        "meals employee(s) only - out of town": "01029", 
        "meals with carrier(s)": "01030",
        "meals with client prospect(s)": "01031",
        "meals with client(s) - in town": "01032",
        "meals with client(s) - out of town": "01033",
        "meals with m&a prospect(s)": "01034",
        
        # Transportation
        "airfare": "01001",
        "car rental": "01002", 
        "gas/fuel": "01007",
        "parking": "01008",
        "taxi/rideshare": "01009",
        "train": "01010",
        
        # Lodging
        "hotel": "01015",
        "lodging": "01015",
        
        # Office Supplies
        "office supplies": "01004",
        "software": "01005",
        
        # Default
        "other": "01028"
    }
    
    PAYMENT_TYPE_MAPPING = {
        "cash": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "personal credit card": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY", 
        "corporate credit card": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "bank transfer": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "check": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY"
    }
    
    # Expense category to type suggestions
    EXPENSE_TYPE_OPTIONS = {
        "Meals & Entertainment": [
            "Meals Employee(s) Only - In Town",
            "Meals Employee(s) Only - Out of Town", 
            "Meals with Carrier(s)",
            "Meals with Client Prospect(s)",
            "Meals with Client(s) - In Town",
            "Meals with Client(s) - Out of Town",
            "Meals with M&A Prospect(s)"
        ],
        "Transportation": [
            "Airfare",
            "Car Rental"
            "Car Rental Gas", 
            "Gas - Leased Car", 
            "Car Mileage", 
            "Monthly Parking",
            "Other Ground Trans. (Shuttle, Bus, Ferry, Subway)",
            "Rideshare (Uber, Lyft)",
            "Train (LongTrip)",
            "Parking/Tolls",
            "Taxi/Limo"
        ],
        "Lodging": [
            "Hotel",
            "Lodging"
        ],
        "Office Supplies": [
            "Office Supplies",
            "Software"
        ]
    }
    
    def get_expense_type_options(self, category: str) -> list:
        """Get available expense types for a category"""
        return self.EXPENSE_TYPE_OPTIONS.get(category, ["Other"])
    
    def map_expense_data_to_entry(self, expense_data: EnhancedExpenseData, report_id: str) -> EnhancedExpenseEntryRequest:
        """Map enhanced expense data to SAP Concur expense entry format"""
        
        # Get expense type code
        expense_type_key = (expense_data.expense_type or "other").lower()
        expense_type_code = self.EXPENSE_TYPE_MAPPING.get(expense_type_key, "01028")
        
        # Get payment type ID
        payment_type_key = (expense_data.payment_type or "personal credit card").lower()
        payment_type_id = self.PAYMENT_TYPE_MAPPING.get(payment_type_key, settings.DEFAULT_PAYMENT_TYPE_ID)
        
        # Create description with business purpose
        description = expense_data.business_purpose or "Business expense"
        if len(description) > 64:
            description = description[:61] + "..."
        
        # Vendor description
        vendor_description = expense_data.vendor or "Unknown Vendor"
        if len(vendor_description) > 64:
            vendor_description = vendor_description[:61] + "..."
        
        # Handle location mapping
        location_city = expense_data.city or settings.DEFAULT_LOCATION_CITY
        location_country = expense_data.country or settings.DEFAULT_LOCATION_COUNTRY
        
        return EnhancedExpenseEntryRequest(
            report_id=report_id,
            expense_type_code=expense_type_code,
            transaction_date=expense_data.transaction_date or datetime.now().strftime('%Y-%m-%d'),
            transaction_amount=expense_data.amount or 0.0,
            transaction_currency_code=expense_data.currency or "USD",
            payment_type_id=payment_type_id,
            description=description,
            vendor_description=vendor_description,
            
            # Meal-specific fields
            meal_type=expense_data.meal_type,
            attendees_count=expense_data.attendees_count or 1,
            client_prospect_name=expense_data.client_prospect_name,
            
            # Location fields (can be enhanced based on extracted data)
            location_city=location_city,
            location_country=location_country,
            location_id=settings.DEFAULT_LOCATION_ID,
            location_name=settings.DEFAULT_LOCATION_NAME,
            location_country_subdivision=settings.DEFAULT_LOCATION_COUNTRY_SUBDIVISION
        )
    
    def validate_expense_data(self, expense_data: EnhancedExpenseData) -> Dict[str, str]:
        """Validate expense data and return errors"""
        errors = {}
        
        if not expense_data.vendor:
            errors["vendor"] = "Vendor is required"
        
        if not expense_data.amount or expense_data.amount <= 0:
            errors["amount"] = "Valid amount is required"
        
        if not expense_data.transaction_date:
            errors["transaction_date"] = "Transaction date is required"
        
        if not expense_data.expense_type:
            errors["expense_type"] = "Expense type is required"
        
        # Meal-specific validations
        if expense_data.expense_category == "Meals & Entertainment":
            if not expense_data.meal_type:
                errors["meal_type"] = "Meal type is required for meals"
            
            if expense_data.attendees_count and expense_data.attendees_count < 1:
                errors["attendees_count"] = "Attendees count must be at least 1"
            
            # Check if client/prospect name is needed
            if expense_data.expense_type and "client" in expense_data.expense_type.lower():
                if not expense_data.client_prospect_name:
                    errors["client_prospect_name"] = "Client/Prospect name is required for client meals"
        
        return errors