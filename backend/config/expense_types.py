# backend/config/expense_types.py

from typing import Dict, List, Any, Optional
from enum import Enum

class ExpenseTypeCategory(str, Enum):
    MEALS = "meals"
    TRANSPORTATION = "transportation"
    LODGING = "lodging"
    AIRFARE = "airfare"

class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    DROPDOWN = "dropdown"
    NUMBER = "number"
    MONEY = "money"
    DATE = "date"
    CHECKBOX = "checkbox"
    ATTENDEE_LIST = "attendee_list"

class ValidationRule:
    def __init__(self, min_val: Optional[float] = None, max_val: Optional[float] = None, 
                 message: Optional[str] = None):
        self.min = min_val
        self.max = max_val
        self.message = message

class FieldDefinition:
    def __init__(self, field_type: FieldType, label: str, required: bool = False,
                 options: Optional[List[Dict[str, str]]] = None, 
                 max_length: Optional[int] = None, placeholder: Optional[str] = None,
                 default: Optional[str] = None, show_when: Optional[Dict[str, str]] = None,
                 validation: Optional[ValidationRule] = None, tooltip: Optional[str] = None):
        self.type = field_type
        self.label = label
        self.required = required
        self.options = options or []
        self.max_length = max_length
        self.placeholder = placeholder
        self.default = default
        self.show_when = show_when
        self.validation = validation
        self.tooltip = tooltip

class AttendeeConfig:
    def __init__(self, required: bool = False, min_attendees: int = 0, 
                 max_attendees: int = 50, attendee_types: Optional[List[str]] = None):
        self.required = required
        self.min_attendees = min_attendees
        self.max_attendees = max_attendees
        self.attendee_types = attendee_types or ["employee", "client"]

class ExpenseTypeConfig:
    def __init__(self, expense_id: str, name: str, description: str, sap_form: str,
                 required_fields: List[str], optional_fields: List[str],
                 hidden_fields: List[str], field_definitions: Dict[str, FieldDefinition],
                 attendees: Optional[AttendeeConfig] = None,
                 validation_rules: Optional[Dict[str, ValidationRule]] = None):
        self.id = expense_id
        self.name = name
        self.description = description
        self.sap_form = sap_form
        self.required_fields = required_fields
        self.optional_fields = optional_fields
        self.hidden_fields = hidden_fields
        self.field_definitions = field_definitions
        self.attendees = attendees
        self.validation_rules = validation_rules or {}

# Meal Type Options
MEAL_TYPE_OPTIONS = [
    {"value": "breakfast", "label": "Breakfast"},
    {"value": "lunch", "label": "Lunch"},
    {"value": "dinner", "label": "Dinner"},
    {"value": "other", "label": "Other"}
]

# Payment Type Options
PAYMENT_TYPE_OPTIONS = [
    {"value": "personal_card", "label": "Personal Credit Card"},
    {"value": "cash", "label": "Cash"},
]

# Currency Options
CURRENCY_OPTIONS = [
    {"value": "USD", "label": "US Dollar (USD)"},
    {"value": "EUR", "label": "Euro (EUR)"},
    {"value": "GBP", "label": "British Pound (GBP)"},
    {"value": "CAD", "label": "Canadian Dollar (CAD)"},
    {"value": "AUD", "label": "Australian Dollar (AUD)"},
    {"value": "JPY", "label": "Japanese Yen (JPY)"}
]

# Business Unit Allocation Options
BU_ALLOCATION_OPTIONS = [
    {"value": "yes", "label": "Yes"},
    {"value": "no", "label": "No"}
]

# Travel Type Options
TRAVEL_TYPE_OPTIONS = [
    {"value": "domestic", "label": "Domestic Travel"},
    {"value": "international", "label": "International Travel"}
]

# Meeting Type Options
MEETING_TYPE_OPTIONS = [
    {"value": "client_facing", "label": "Client/Carrier-Facing"},
    {"value": "internal", "label": "Internal Employee Meeting"},
    {"value": "training", "label": "Training/Workshop"},
    {"value": "conference", "label": "Conference/Event"}
]

# Common Field Definitions
COMMON_FIELD_DEFINITIONS = {
    "expense_type": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Expense Type",
        required=True
    ),
    "transaction_date": FieldDefinition(
        field_type=FieldType.DATE,
        label="Transaction Date",
        required=True
    ),
    "business_purpose": FieldDefinition(
        field_type=FieldType.TEXTAREA,
        label="Business Purpose",
        required=True,
        max_length=255,
        placeholder="Describe the business purpose of this expense"
    ),
    "vendor_description": FieldDefinition(
        field_type=FieldType.TEXT,
        label="Vendor/Restaurant Name",
        required=True,
        max_length=64
    ),
    "city_of_purchase": FieldDefinition(
        field_type=FieldType.TEXT,
        label="City of Purchase",
        required=True,
        max_length=64
    ),
    "currency": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Currency",
        required=True,
        default="USD",
        options=CURRENCY_OPTIONS
    ),
    "payment_type": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Payment Type",
        required=True,
        options=PAYMENT_TYPE_OPTIONS
    ),
    "amount": FieldDefinition(
        field_type=FieldType.MONEY,
        label="Amount",
        required=True,
        validation=ValidationRule(min_val=0.01, max_val=10000, 
                                message="Amount must be between $0.01 and $10,000")
    ),
    "meal_type": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Meal Type",
        required=True,
        options=MEAL_TYPE_OPTIONS
    ),
    "business_unit_allocation": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Allocate to Another Business Unit?",
        required=False,
        options=BU_ALLOCATION_OPTIONS
    ),
    "business_unit": FieldDefinition(
        field_type=FieldType.TEXT,
        label="Business Unit",
        required=False,
        max_length=50,
        show_when={"field": "business_unit_allocation", "value": "yes"}
    ),
    "comment": FieldDefinition(
        field_type=FieldType.TEXTAREA,
        label="Comment",
        required=False,
        max_length=500,
        placeholder="Additional details or notes"
    ),
    "travel_type": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Travel Type",
        required=True,
        options=TRAVEL_TYPE_OPTIONS
    ),
    "meeting_type": FieldDefinition(
        field_type=FieldType.DROPDOWN,
        label="Meeting Type",
        required=True,
        options=MEETING_TYPE_OPTIONS
    ),
    "attendees": FieldDefinition(
        field_type=FieldType.ATTENDEE_LIST,
        label="Attendees",
        required=True
    )
}

# Expense Type Configurations
EXPENSE_TYPE_CONFIGS = {
    ExpenseTypeCategory.MEALS: {
        "parent_category": "04. Meals & Entertainment",
        "types": {
            "meals_employee_in_town": ExpenseTypeConfig(
                expense_id="meals_employee_in_town",
                name="Meals Employee(s) Only - In Town",
                description="Meals with only company employees while in town",
                sap_form="AJG Non-VAT MealsEEOnly Attendees",
                required_fields=[
                    "expense_type", "transaction_date", "business_purpose", 
                    "meal_type", "vendor_description", "city_of_purchase", 
                    "currency", "payment_type", "amount"
                ],
                optional_fields=[
                    "comment", "business_unit_allocation", "business_unit"
                ],
                hidden_fields=[
                    "country_code", "domestic_international", "org_units"
                ],
                field_definitions={
                    **COMMON_FIELD_DEFINITIONS
                },
                attendees=AttendeeConfig(
                    required=False,
                    max_attendees=20,
                    attendee_types=["employee"]
                )
            ),
            "meals_client_in_town": ExpenseTypeConfig(
                expense_id="meals_client_in_town",
                name="Meals with Client(s) - In Town",
                description="Business meals with clients while in town",
                sap_form="AJG Non-VAT Client Meals w/ Attendees",
                required_fields=[
                    "expense_type", "transaction_date", "business_purpose", 
                    "meal_type", "vendor_description", "city_of_purchase", 
                    "currency", "payment_type", "amount", "attendees"
                ],
                optional_fields=[
                    "comment", "business_unit_allocation", "business_unit"
                ],
                hidden_fields=[
                    "country_code", "domestic_international", "org_units"
                ],
                field_definitions={
                    **COMMON_FIELD_DEFINITIONS
                },
                attendees=AttendeeConfig(
                    required=True,
                    min_attendees=1,
                    max_attendees=50,
                    attendee_types=["employee", "client", "prospect", "supplier", "business_guest"]
                )
            ),
            "meals_client_out_of_town": ExpenseTypeConfig(
                expense_id="meals_client_out_of_town",
                name="Meals with Client(s) - Out of Town",
                description="Business meals with clients while traveling",
                sap_form="AJG Non-VAT Client Meals w/ Attendees+Trvl Type",
                required_fields=[
                    "expense_type", "transaction_date", "business_purpose", 
                    "meal_type", "vendor_description", "city_of_purchase", 
                    "currency", "payment_type", "amount", "attendees", "travel_type"
                ],
                optional_fields=[
                    "comment", "business_unit_allocation", "business_unit"
                ],
                hidden_fields=[
                    "country_code", "domestic_international", "org_units"
                ],
                field_definitions={
                    **COMMON_FIELD_DEFINITIONS
                },
                attendees=AttendeeConfig(
                    required=True,
                    min_attendees=1,
                    max_attendees=50,
                    attendee_types=["employee", "client", "prospect", "supplier", "business_guest"]
                )
            ),
            "meeting_catering": ExpenseTypeConfig(
                expense_id="meeting_catering",
                name="Meeting/Catering",
                description="Catering for business meetings",
                sap_form="AJG Non-VAT Meeting/Catering Attendees",
                required_fields=[
                    "expense_type", "transaction_date", "business_purpose", 
                    "meeting_type", "vendor_description", "city_of_purchase", 
                    "currency", "payment_type", "amount", "attendees"
                ],
                optional_fields=[
                    "comment", "business_unit_allocation", "business_unit"
                ],
                hidden_fields=[
                    "country_code", "domestic_international", "org_units"
                ],
                field_definitions={
                    **{k: v for k, v in COMMON_FIELD_DEFINITIONS.items() if k != "meal_type"},
                    "meeting_type": COMMON_FIELD_DEFINITIONS["meeting_type"]
                },
                attendees=AttendeeConfig(
                    required=True,
                    min_attendees=1,
                    max_attendees=100,
                    attendee_types=["employee", "client", "prospect", "supplier", "business_guest"]
                )
            )
        }
    }
}

# AI Mapping Prompts
AI_MAPPING_PROMPTS = {
    "meal_type_detection": """
    Based on the receipt content, determine the most appropriate meal type:
    - breakfast: Morning meals, coffee meetings, breakfast items
    - lunch: Midday meals, business lunch meetings
    - dinner: Evening meals, dinner meetings, late dining
    - snacks: Light refreshments, coffee, pastries, bar snacks
    - other: Mixed meals or unclear timing
    
    Return only the meal type value.
    """,
    
    "payment_type_detection": """
    Based on the receipt content and transaction details, determine payment type:
    - corporate_card: If company credit card used
    - personal_card: If personal credit card used (look for personal names)
    - cash: If cash payment mentioned
    - bank_transfer: If wire transfer or bank payment
    - check: If check payment mentioned
    
    Return only the payment type value.
    """,

    "business_purpose_generation": """
    Generate a professional business purpose based on:
    - Receipt vendor/restaurant name
    - Meal type and timing
    - Location information
    - Any visible meeting/business context
    
    Keep it concise (under 100 characters) and professional.
    Examples: "Client lunch meeting", "Business dinner with prospects", "Team meeting catering"
    """
}

def get_expense_type_from_receipt(extracted_data: Dict[str, Any]) -> str:
    """Simple heuristics for expense type detection"""
    vendor = extracted_data.get('vendor', '').lower()
    amount = extracted_data.get('amount', 0)
    
    # Simple heuristics - can be enhanced with AI
    if 'starbucks' in vendor or 'coffee' in vendor:
        return 'meals_employee_in_town'
    
    if amount > 100:
        return 'meals_client_in_town'  # Likely client meal if expensive
    
    return 'meals_employee_in_town'  # Default

def map_fields_to_expense_type(expense_type_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map extracted data to expense type fields"""
    mapped_data = {}
    
    # Map common fields
    field_mapping = {
        'vendor': 'vendor_description',
        'amount': 'amount',
        'transaction_date': 'transaction_date',
        'city': 'city_of_purchase',
        'currency': 'currency',
        'payment_type': 'payment_type',
        'business_purpose': 'business_purpose'
    }
    
    for source_field, target_field in field_mapping.items():
        if source_field in extracted_data and extracted_data[source_field] is not None:
            mapped_data[target_field] = extracted_data[source_field]
    
    return mapped_data