from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EnhancedExpenseData(BaseModel):
    """Enhanced expense data model matching SAP Concur fields"""
    
    # Main categorization
    expense_category: Optional[str] = None  # Meals & Entertainment, Lodging, etc.
    expense_type: Optional[str] = None      # Specific SAP expense type
    
    # Meal-specific fields
    meal_type: Optional[str] = None         # Breakfast, Lunch, Dinner, Other
    attendees_count: Optional[int] = 1      # Number of attendees
    client_prospect_name: Optional[str] = None  # Client/Prospect company name
    
    # Standard fields
    transaction_date: Optional[str] = None
    business_purpose: Optional[str] = None
    vendor: Optional[str] = None            # Maps to Vendor field in SAP
    city: Optional[str] = None
    country: Optional[str] = None
    payment_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    comment: Optional[str] = None

class EnhancedExpenseEntryRequest(BaseModel):
    """Enhanced expense entry request for SAP Concur API"""
    
    report_id: str
    expense_type_code: str       # Will be mapped from expense_type
    transaction_date: str
    transaction_amount: float
    transaction_currency_code: str
    payment_type_id: str 
    description: str                        # Business purpose
    vendor_description: str                 # Vendor name
    
    # Meal-specific fields
    meal_type: Optional[str] = None
    attendees_count: Optional[int] = 1
    client_prospect_name: Optional[str] = None
    
    # Location fields
    location_id: str
    location_name: str
    location_city: str
    location_country_subdivision: str
    location_country: str

    # Standard fields
    is_personal: bool = False
    is_billable: bool = False
    tax_receipt_type: str = "R"
    
    # Business unit allocation (if needed)
    allocate_to_business_unit: Optional[str] = None
    business_unit: Optional[str] = None

class ExpenseData(BaseModel):
    expense_type: Optional[str] = None
    transaction_date: Optional[str] = None
    business_purpose: Optional[str] = None
    vendor: Optional[str] = None
    starting_city: Optional[str] = None
    country: Optional[str] = None
    payment_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    comment: Optional[str] = None
    meal_type: Optional[str] = None
    custom9: Optional[str] = None 


class ExpenseEntryRequest(BaseModel):
    report_id: str
    expense_type_code: str
    transaction_date: str
    transaction_amount: float
    transaction_currency_code: str
    payment_type_id: str
    description: str
    vendor_description: str
    location_id: str
    location_name: str
    location_city: str
    location_country_subdivision: str
    location_country: str
    is_personal: bool = False
    is_billable: bool = False
    tax_receipt_type: str = "R"