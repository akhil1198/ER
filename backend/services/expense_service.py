from datetime import datetime
from typing import Dict
from models.expense import ExpenseData, ExpenseEntryRequest
from config.settings import settings

class ExpenseService:
    
    # Mapping configurations
    EXPENSE_TYPE_MAPPING = {
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
    
    PAYMENT_TYPE_MAPPING = {
        "credit card": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "cash": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "bank transfer": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "check": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "other": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY"
    }
    
    def map_expense_data_to_entry(self, expense_data: ExpenseData, report_id: str) -> ExpenseEntryRequest:
        """Map extracted expense data to SAP Concur expense entry format"""
        
        # Get expense type code
        expense_type_key = (expense_data.expense_type or "other").lower()
        expense_type_code = self.EXPENSE_TYPE_MAPPING.get(expense_type_key, "01028")
        
        # Get payment type ID
        payment_type_key = (expense_data.payment_type or "credit card").lower()
        payment_type_id = self.PAYMENT_TYPE_MAPPING.get(payment_type_key, settings.DEFAULT_PAYMENT_TYPE_ID)
        
        # Create description with SAP Concur length limits (64 characters max)
        description_parts = []
        if expense_data.business_purpose:
            description_parts.append(expense_data.business_purpose)
        
        if not description_parts:
            if expense_data.vendor:
                description_parts.append(f"Expense at {expense_data.vendor}")
            else:
                description_parts.append("Business expense")
        
        # Join and truncate to 64 characters
        description = " - ".join(description_parts)
        if len(description) > 64:
            description = description[:61] + "..."
        
        # Truncate vendor description to safe length
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
            location_id=settings.DEFAULT_LOCATION_ID,
            location_name=settings.DEFAULT_LOCATION_NAME,
            location_city=settings.DEFAULT_LOCATION_CITY,
            location_country_subdivision=settings.DEFAULT_LOCATION_COUNTRY_SUBDIVISION,
            location_country=settings.DEFAULT_LOCATION_COUNTRY
        )