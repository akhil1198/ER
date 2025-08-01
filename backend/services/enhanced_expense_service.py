from datetime import datetime
from typing import Dict, List, Any
from models.expense import EnhancedExpenseData, EnhancedExpenseEntryRequest
from config.settings import settings

class EnhancedExpenseService:
    
    # Comprehensive expense type mapping based on actual SAP Concur data
    EXPENSE_TYPE_MAPPING = {
        # 01. Airfare
        "airfare non-employee": "AIRFR",
        "airfare employee": "01061", 
        "airfare spouse/significant other": "01062",
        "airline ancillary fees": "01065",
        "airline ancillary fees (wifi, baggage, sky cap tips)": "01065",
        "ggb tp airfare - employee": "01066",
        "reticketing/cancellation fee": "01063",
        "travel agency fees": "01064",
        
        # 02. Lodging
        "hotel stay": "LODNG",
        "lodging": "LODNG",
        "hotel": "LODNG",
        "early check-in/out fee": "01068",
        "hotel ancillary fees": "01069",
        "hotel ancillary fees (parking, internet, health club, laundry)": "01069",
        "prepaid hotel cancellation": "01067",
        "prepaid hotel deposit": "01070",
        
        # 03. Transportation
        "car mileage": "MILEG",
        "car rental": "CARRT",
        "car rental gas": "01074",
        "gas - leased car": "01071",
        "monthly parking": "01145",
        "other ground trans. (shuttle, bus, ferry, subway)": "01073",
        "parking/tolls": "PARKG",
        "rideshare (uber, lyft)": "01072",
        "taxi/limo": "TAXIX",
        "train (longtrip)": "01025",
        
        # 04. Meals & Entertainment
        "meals employee(s) only - in town": "01028",
        "meals employee(s) only - out of town": "01075",
        "meals with carrier(s)": "01039",
        "meals with client prospect(s)": "01080",
        "meals with client(s) - in town": "01027",
        "meals with client(s) - out of town": "01076",
        "meals with m&a prospect(s)": "01079",
        "meals with supplier(s)": "01077",
        "meals with underwriter(s)": "01078",
        "other entertainment - client": "BUSML",
        "tickets - client-facing (skybox, sporting event, theater)": "01029",
        "tickets - non-client facing (skybox, sporting event, theater)": "01041",
        
        # 05. Meetings
        "meetings client/carrier-facing - activity/entertainment": "01087",
        "meetings client/carrier-facing - airfare": "01088",
        "meetings client/carrier-facing - lodging": "01081",
        "meetings client/carrier-facing - meals": "01082",
        "meetings client/carrier-facing - other": "01083",
        "meetings client/carrier-facing - transportation": "01089",
        "meetings employees only - activity/entertainment": "01090",
        "meetings employees only - airfare": "01091",
        "meetings employees only - lodging": "01084",
        "meetings employees only - meals": "01085",
        "meetings employees only - other": "01086",
        "meetings employees only - transportation": "01092",
        
        # 06. Marketing
        "advertising expense": "01093",
        "branded merchandise": "01094",
        "client gifts": "01095",
        "group membership - prospecting organization": "01096",
        
        # 07. Seminars & Education
        "conferences & training - professional development": "01103",
        "conferences & training - sales/business development": "01104",
        "insurance continuing ed": "01106",
        "insurance exam fees": "01107",
        "non-insurance continuing ed/exam fees": "01108",
        
        # 08. Taxes, Licenses, & Fees
        "club dues (golf, hunting, social, etc)": "01114",
        "ggb tp club dues": "01113",
        "insurance licenses-misc fees (nipr)": "01115",
        "insurance licenses-processing fees": "01116",
        "insurance licenses-state fees": "01118",
        "professional dues - professional designation": "01119",
        "professional dues - sales/business development": "01120",
        
        # 09. Telecommunications
        "cellular int'l roaming charges(only)": "01121",
        "cellular phone": "CELPH",
        "teleworker - home internet/landline": "01126",
        
        # 10. Office Expense
        "breakroom supplies": "01148",
        "computer supplies hardware": "01131",
        "computer supplies software": "01132",
        "employee gifts (flowers, retirement)": "AWRDS",
        "express mail": "01138",
        "it/software subscriptions": "01141",
        "magazine/periodicals subscriptions": "01143",
        "office supplies": "01007",
        "out of town travel - other (visas, fx, etc)": "01146",
        "postage": "POSTG",
        "print/copy for clients/prospects": "01006",
        "print/copy supplies & maintenance": "01153",
        "service awards (gb only)": "01147",
        
        # 11. Client Reimbursed Travel (CRT)
        "crt agency fees": "01164",
        "crt airline": "01165",
        "crt airline ancillary fees": "01166",
        "crt car mileage": "01167",
        "crt car rental": "01168",
        "crt car rental gas": "01169",
        "crt entertainment & bus dev": "01170",
        "crt ground trans": "01171",
        "crt hotel ancillary fees": "01172",
        "crt hotel stay": "01173",
        "crt meals-employee(s) only": "01174",
        "crt meeting expense": "01175",
        "crt other": "01176",
        "crt parking/tolls": "01177",
        "crt prepaid hotel deposit": "01178",
        "crt re-ticketing cancellation fee": "01179",
        "crt room tax": "01180",
        "crt subscriptions magazine/periodicals": "01181",
        "crt train": "01182",
        
        # 13. Non-reimbursable Personal Expenses
        "clearing transactions(concur administrator only)": "01186",
        "paid through ap": "01187",
        "personal expense": "01188",

    }
    
    # Travel type mapping data
    TRAVEL_TYPE_MAPPING = {
        
    }

    # Payment type mapping based on actual SAP Concur data
    PAYMENT_TYPE_MAPPING = {
        "cash": "CASH",
        "personal credit card": "1007", 
    }

    # Expense category to type options based on actual SAP Concur structure
    EXPENSE_TYPE_OPTIONS = {
        "01. Airfare": [
            "Airfare Non-Employee",
            "Airfare-Employee", 
            "Airfare-Spouse/Significant Other",
            "Airline Ancillary Fees (WiFi, Baggage, Sky Cap Tips)",
            "GGB TP Airfare - Employee",
            "Reticketing/Cancellation Fee",
            "Travel Agency Fees"
        ],
        "02. Lodging": [
            "Early Check-In/Out Fee",
            "Hotel Ancillary Fees (parking, internet, health club, laundry)",
            "Hotel Stay",
            "Prepaid Hotel Cancellation", 
            "Prepaid Hotel Deposit"
        ],
        "03. Transportation": [
            "Car Mileage",
            "Car Rental",
            "Car Rental Gas",
            "Gas - Leased Car",
            "Monthly Parking",
            "Other Ground Trans. (Shuttle, Bus, Ferry, Subway)",
            "Parking/Tolls",
            "Rideshare (Uber, Lyft)",
            "Taxi/Limo",
            "Train (LongTrip)"
        ],
        "04. Meals & Entertainment": [
            "Meals Employee(s) Only - In Town",
            "Meals Employee(s) Only - Out of Town",
            "Meals with Carrier(s)",
            "Meals with Client Prospect(s)",
            "Meals with Client(s) - In Town", 
            "Meals with Client(s) - Out of Town",
            "Meals with M&A Prospect(s)",
            "Meals with Supplier(s)",
            "Meals with Underwriter(s)",
            "Other Entertainment - Client",
            "Tickets - Client-Facing (skybox, sporting event, theater)",
            "Tickets - Non-Client Facing (skybox, sporting event, theater)"
        ],
        "05. Meetings": [
            "Meetings Client/Carrier-Facing - Activity/Entertainment",
            "Meetings Client/Carrier-Facing - Airfare",
            "Meetings Client/Carrier-Facing - Lodging",
            "Meetings Client/Carrier-Facing - Meals", 
            "Meetings Client/Carrier-Facing - Other (room, A/V, etc.)",
            "Meetings Client/Carrier-Facing - Transportation",
            "Meetings Employees Only - Activity/Entertainment",
            "Meetings Employees Only - Airfare",
            "Meetings Employees Only - Lodging",
            "Meetings Employees Only - Meals",
            "Meetings Employees Only - Other (room, A/V, etc.)",
            "Meetings Employees Only - Transportation"
        ],
        "06. Marketing": [
            "Advertising Expense",
            "Branded Merchandise", 
            "Client Gifts",
            "Group Membership - Prospecting Organization"
        ],
        "07. Seminars & Education": [
            "Conferences & Training - Professional Development",
            "Conferences & Training - Sales/Business Development",
            "Insurance Continuing Ed",
            "Insurance Exam Fees",
            "Non-Insurance Continuing Ed/Exam Fees"
        ],
        "08. Taxes, Licenses, & Fees": [
            "Club Dues (golf, hunting, social, etc)",
            "GGB TP Club Dues",
            "Insurance Licenses-Misc Fees (NIPR)",
            "Insurance Licenses-Processing Fees",
            "Insurance Licenses-State Fees",
            "Professional Dues - Professional Designation (AICPA, SHRM, CLU's)",
            "Professional Dues - Sales/Business Development (RIMS, CII)"
        ],
        "09. Telecommunications": [
            "Cellular Int'l Roaming Charges(only)",
            "Cellular Phone",
            "Teleworker - Home Internet/Landline"
        ],
        "10. Office Expense": [
            "Breakroom Supplies",
            "Computer Supplies Hardware",
            "Computer Supplies Software",
            "Employee Gifts (flowers, retirement)",
            "Express Mail",
            "IT/Software Subscriptions",
            "Magazine/Periodicals Subscriptions",
            "Office Supplies",
            "Out of Town Travel - Other (Visas, FX, etc)",
            "Postage",
            "Print/Copy for Clients/Prospects",
            "Print/Copy Supplies & Maintenance",
            "Service Awards (GB Only)"
        ],
        "11. Client Reimbursed Travel (CRT)": [
            "CRT Agency Fees",
            "CRT Airline", 
            "CRT Airline Ancillary Fees (WiFi, Baggage, Sky Cap Tips)",
            "CRT Car Mileage",
            "CRT Car Rental",
            "CRT Car Rental Gas",
            "CRT Entertainment & Bus Dev",
            "CRT Ground Trans (Shuttle, Bus, Ferry, Subway)",
            "CRT Hotel Ancillary Fees (parking, internet, health club, laundry)",
            "CRT Hotel Stay",
            "CRT Meals-Employee(s) Only",
            "CRT Meeting Expense", 
            "CRT Other",
            "CRT Parking/Tolls",
            "CRT Prepaid Hotel Deposit",
            "CRT Re-ticketing Cancellation Fee",
            "CRT Room Tax",
            "CRT Subscriptions Magazine/Periodicals",
            "CRT Train"
        ],
        "13. Non-reimbursable Personal Expenses": [
            "Clearing Transactions(Concur Administrator only)",
            "Paid Through AP",
            "Personal Expense"
        ]
    }
    
    # Mapping for common expense type searches/aliases
    EXPENSE_TYPE_ALIASES = {
        "airfare": "01061",  # Default to employee airfare
        "flight": "01061",
        "airplane": "01061", 
        "hotel": "LODNG",
        "accommodation": "LODNG",
        "rental car": "CARRT",
        "car": "CARRT",
        "uber": "01072",
        "lyft": "01072", 
        "taxi": "TAXIX",
        "meal": "01028",  # Default to employee meals in town
        "lunch": "01028",
        "dinner": "01028",
        "breakfast": "01028",
        "gas": "01071",  # Default to leased car gas
        "fuel": "01071",
        "parking": "PARKG",
        "toll": "PARKG",
        "train": "01025",
        "subway": "01073",
        "bus": "01073",
        "software": "01132",
        "subscription": "01141",
        "office": "01007",
        "supplies": "01007"
    }
    
    
    def generate_expense_form(self, expense_type_id: str) -> Dict[str, Any]:
        """Generate dynamic form configuration based on expense type"""
        
        # Define field configurations for different expense types
        EXPENSE_TYPE_FORMS = {
            "rideshare_uber_lyft": {
                "expense_type": {
                    "id": "rideshare_uber_lyft",
                    "name": "Rideshare (Uber, Lyft)",
                    "description": "Rideshare transportation services",
                    "category": "Transportation",
                    "sap_form": "AJG Non-VAT Transportation"
                },
                "sections": [
                    {
                        "title": "Trip Information",
                        "fields": [
                            {
                                "name": "transaction_date",
                                "type": "date",
                                "label": "Trip Date",
                                "required": True,
                                "validation": {"required": True}
                            },
                            {
                                "name": "business_purpose", 
                                "type": "textarea",
                                "label": "Business Purpose",
                                "required": True,
                                "placeholder": "e.g., Client meeting transportation, Airport transfer",
                                "validation": {"required": True, "maxLength": 255}
                            },
                            {
                                "name": "travel_type",
                                "type": "dropdown",
                                "label": "Travel Type", 
                                "required": True,
                                "options": [
                                    {"value": "domestic", "label": "Domestic"},
                                    {"value": "international", "label": "International"}
                                ],
                                "default": "domestic"
                            },
                            {
                                "name": "starting_city",
                                "type": "text",
                                "label": "Starting City",
                                "required": True,
                                "validation": {"required": True, "maxLength": 64}
                            }
                        ]
                    },
                    {
                        "title": "Payment Details",
                        "fields": [
                            {
                                "name": "vendor",
                                "type": "text", 
                                "label": "Rideshare Company",
                                "required": True,
                                "placeholder": "Uber, Lyft, etc.",
                                "validation": {"required": True, "maxLength": 64}
                            },
                            {
                                "name": "amount",
                                "type": "money",
                                "label": "Trip Cost",
                                "required": True,
                                "validation": {"required": True, "min": 0.01}
                            },
                            {
                                "name": "currency",
                                "type": "dropdown",
                                "label": "Currency",
                                "required": True,
                                "options": [
                                    {"value": "USD", "label": "US Dollar (USD)"},
                                    {"value": "EUR", "label": "Euro (EUR)"},
                                    {"value": "GBP", "label": "British Pound (GBP)"}
                                ],
                                "default": "USD"
                            },
                            {
                                "name": "payment_type",
                                "type": "dropdown", 
                                "label": "Payment Method",
                                "required": True,
                                "options": [
                                    {"value": "personal_card", "label": "Personal Credit Card"},
                                    {"value": "cash", "label": "Cash"}
                                ],
                                "default": "personal_card"
                            }
                        ]
                    },
                    {
                        "title": "Additional Information",
                        "fields": [
                            {
                                "name": "country",
                                "type": "text",
                                "label": "Country",
                                "required": False,
                                "default": "US",
                                "validation": {"maxLength": 2}
                            },
                            {
                                "name": "comment",
                                "type": "textarea",
                                "label": "Trip Details",
                                "required": False,
                                "placeholder": "Destination, trip purpose, or additional notes",
                                "validation": {"maxLength": 500}
                            }
                        ]
                    }
                ]
            },
            
            "meals_client_in_town": {
                "expense_type": {
                    "id": "meals_client_in_town", 
                    "name": "Meals with Client(s) - In Town",
                    "description": "Business meals with clients while in town",
                    "category": "Meals & Entertainment",
                    "sap_form": "AJG Non-VAT Client Meals w/ Attendees"
                },
                "sections": [
                    {
                        "title": "Meal Information",
                        "fields": [
                            {
                                "name": "transaction_date",
                                "type": "date",
                                "label": "Meal Date",
                                "required": True,
                                "validation": {"required": True}
                            },
                            {
                                "name": "business_purpose",
                                "type": "textarea", 
                                "label": "Business Purpose",
                                "required": True,
                                "placeholder": "e.g., Client lunch meeting, Prospect dinner discussion",
                                "validation": {"required": True, "maxLength": 255}
                            },
                            {
                                "name": "meal_type",
                                "type": "dropdown",
                                "label": "Meal Type",
                                "required": True,
                                "options": [
                                    {"value": "breakfast", "label": "Breakfast"},
                                    {"value": "lunch", "label": "Lunch"},
                                    {"value": "dinner", "label": "Dinner"},
                                    {"value": "other", "label": "Other"}
                                ]
                            },
                            {
                                "name": "vendor",
                                "type": "text",
                                "label": "Restaurant Name",
                                "required": True,
                                "validation": {"required": True, "maxLength": 64}
                            }
                        ]
                    },
                    {
                        "title": "Attendee Information", 
                        "fields": [
                            {
                                "name": "attendees_count",
                                "type": "number",
                                "label": "Number of Attendees",
                                "required": True,
                                "validation": {"required": True, "min": 2},
                                "default": 2
                            },
                            {
                                "name": "client_prospect_name",
                                "type": "text",
                                "label": "Client/Prospect Company",
                                "required": True,
                                "placeholder": "Company name or client name",
                                "validation": {"required": True, "maxLength": 100}
                            }
                        ]
                    },
                    {
                        "title": "Payment Details",
                        "fields": [
                            {
                                "name": "amount",
                                "type": "money",
                                "label": "Total Amount",
                                "required": True, 
                                "validation": {"required": True, "min": 0.01}
                            },
                            {
                                "name": "currency",
                                "type": "dropdown",
                                "label": "Currency",
                                "required": True,
                                "options": [
                                    {"value": "USD", "label": "US Dollar (USD)"},
                                    {"value": "EUR", "label": "Euro (EUR)"},
                                    {"value": "GBP", "label": "British Pound (GBP)"}
                                ],
                                "default": "USD"
                            },
                            {
                                "name": "payment_type",
                                "type": "dropdown",
                                "label": "Payment Method", 
                                "required": True,
                                "options": [
                                    {"value": "personal_card", "label": "Personal Credit Card"},
                                    {"value": "cash", "label": "Cash"}
                                ],
                                "default": "personal_card"
                            }
                        ]
                    },
                    {
                        "title": "Location & Additional Info",
                        "fields": [
                            {
                                "name": "city",
                                "type": "text",
                                "label": "City",
                                "required": True,
                                "validation": {"required": True, "maxLength": 64}
                            },
                            {
                                "name": "country", 
                                "type": "text",
                                "label": "Country",
                                "required": False,
                                "default": "US",
                                "validation": {"maxLength": 2}
                            },
                            {
                                "name": "comment",
                                "type": "textarea",
                                "label": "Additional Details",
                                "required": False,
                                "placeholder": "Additional details about the meal or attendees",
                                "validation": {"maxLength": 500}
                            }
                        ]
                    }
                ]
            },

            "meals_employee_in_town": {
                "expense_type": {
                    "id": "meals_employee_in_town",
                    "name": "Meals Employee(s) Only - In Town", 
                    "description": "Meals with only company employees while in town",
                    "category": "Meals & Entertainment",
                    "sap_form": "AJG Non-VAT MealsEEOnly Attendees"
                },
                "sections": [
                    {
                        "title": "Meal Information",
                        "fields": [
                            {
                                "name": "transaction_date",
                                "type": "date",
                                "label": "Meal Date",
                                "required": True,
                                "validation": {"required": True}
                            },
                            {
                                "name": "business_purpose",
                                "type": "textarea",
                                "label": "Business Purpose", 
                                "required": True,
                                "placeholder": "e.g., Team working lunch, Employee meeting meal",
                                "validation": {"required": True, "maxLength": 255}
                            },
                            {
                                "name": "meal_type",
                                "type": "dropdown",
                                "label": "Meal Type",
                                "required": True,
                                "options": [
                                    {"value": "breakfast", "label": "Breakfast"},
                                    {"value": "lunch", "label": "Lunch"},
                                    {"value": "dinner", "label": "Dinner"},
                                    {"value": "other", "label": "Other"}
                                ]
                            },
                            {
                                "name": "vendor",
                                "type": "text",
                                "label": "Restaurant Name",
                                "required": True,
                                "validation": {"required": True, "maxLength": 64}
                            },
                            {
                                "name": "attendees_count",
                                "type": "number", 
                                "label": "Number of Employees",
                                "required": False,
                                "validation": {"min": 1},
                                "default": 1
                            }
                        ]
                    },
                    {
                        "title": "Payment Details",
                        "fields": [
                            {
                                "name": "amount",
                                "type": "money",
                                "label": "Total Amount",
                                "required": True,
                                "validation": {"required": True, "min": 0.01}
                            },
                            {
                                "name": "currency",
                                "type": "dropdown",
                                "label": "Currency",
                                "required": True,
                                "options": [
                                    {"value": "USD", "label": "US Dollar (USD)"},
                                    {"value": "EUR", "label": "Euro (EUR)"},
                                    {"value": "GBP", "label": "British Pound (GBP)"}
                                ],
                                "default": "USD"
                            },
                            {
                                "name": "payment_type",
                                "type": "dropdown",
                                "label": "Payment Method",
                                "required": True,
                                "options": [
                                    {"value": "personal_card", "label": "Personal Credit Card"}, 
                                    {"value": "cash", "label": "Cash"}
                                ],
                                "default": "personal_card"
                            }
                        ]
                    },
                    {
                        "title": "Location & Additional Info",
                        "fields": [
                            {
                                "name": "city",
                                "type": "text",
                                "label": "City",
                                "required": True,
                                "validation": {"required": True, "maxLength": 64}
                            },
                            {
                                "name": "country",
                                "type": "text",
                                "label": "Country",
                                "required": False,
                                "default": "US",
                                "validation": {"maxLength": 2}
                            },
                            {
                                "name": "comment",
                                "type": "textarea",
                                "label": "Additional Details", 
                                "required": False,
                                "placeholder": "Additional details about the meal",
                                "validation": {"maxLength": 500}
                            }
                        ]
                    }
                ]
            }
        }
        
        # Normalize expense type ID
        normalized_id = expense_type_id.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
        
        # Map common variations to our form IDs
        if "rideshare" in normalized_id or "uber" in normalized_id or "lyft" in normalized_id:
            normalized_id = "rideshare_uber_lyft"
        elif "meals_with_client" in normalized_id and "in_town" in normalized_id:
            normalized_id = "meals_client_in_town"
        elif "meals_employee" in normalized_id and "in_town" in normalized_id:
            normalized_id = "meals_employee_in_town"
        
        # Return the form configuration
        return EXPENSE_TYPE_FORMS.get(normalized_id, self._get_default_form(expense_type_id))

    def _get_default_form(self, expense_type_id: str) -> Dict[str, Any]:
        """Return a default form configuration for unknown expense types"""
        return {
            "expense_type": {
                "id": expense_type_id,
                "name": expense_type_id.replace('_', ' ').title(),
                "description": "Basic expense form",
                "category": "Other",
                "sap_form": "Basic Form"
            },
            "sections": [
                {
                    "title": "Basic Information",
                    "fields": [
                        {
                            "name": "transaction_date",
                            "type": "date", 
                            "label": "Transaction Date",
                            "required": True
                        },
                        {
                            "name": "business_purpose",
                            "type": "textarea",
                            "label": "Business Purpose",
                            "required": True
                        },
                        {
                            "name": "vendor",
                            "type": "text",
                            "label": "Vendor",
                            "required": True
                        },
                        {
                            "name": "amount",
                            "type": "money",
                            "label": "Amount", 
                            "required": True
                        }
                    ]
                }
            ]
        }

    async def map_data_to_expense_type(self, expense_type: str, extracted_data: Dict[str, Any]) -> 'MappingResult':
        """Map extracted data to specific expense type format"""
        
        # Create a mapping result object
        class MappingResult:
            def __init__(self, mapped_data, expense_type_info, validation_errors):
                self.mapped_data = mapped_data
                self.expense_type = expense_type_info
                self.validation_errors = validation_errors
        
        class ExpenseTypeInfo:
            def __init__(self, name, description, category):
                self.name = name
                self.description = description
                self.category = category
        
        # Map the data based on expense type
        if "rideshare" in expense_type.lower() or "uber" in expense_type.lower() or "lyft" in expense_type.lower():
            print("Mapping to Rideshare (Uber, Lyft) expense type", )
            mapped_data = {
                "transaction_date": extracted_data.get("transaction_date"),
                "business_purpose": extracted_data.get("business_purpose"),
                "travel_type": extracted_data.get("travel_type", "Domestic"),
                "starting_city": extracted_data.get("starting_city"),
                "country": extracted_data.get("country", "US"),
                "payment_type": extracted_data.get("payment_type"),
                "amount": extracted_data.get("amount"),
                "currency": extracted_data.get("currency", "USD"),
                "vendor": extracted_data.get("vendor"),
                "comment": extracted_data.get("comment"),
                "expense_type": extracted_data.get("expense_type")
            }
            expense_type_info = ExpenseTypeInfo(
                name="Rideshare (Uber, Lyft)",
                description="Rideshare transportation services",
                category="Transportation"
            )
        
        elif "meals with client" in expense_type.lower():
            mapped_data = {
                "transaction_date": extracted_data.get("transaction_date"),
                "business_purpose": extracted_data.get("business_purpose"),
                "meal_type": extracted_data.get("meal_type"),
                "vendor": extracted_data.get("vendor"),
                "city": extracted_data.get("city"),
                "country": extracted_data.get("country", "US"),
                "payment_type": extracted_data.get("payment_type"),
                "amount": extracted_data.get("amount"),
                "currency": extracted_data.get("currency", "USD"),
                "attendees_count": extracted_data.get("attendees_count", 2),
                "client_prospect_name": extracted_data.get("client_prospect_name"),
                "comment": extracted_data.get("comment"),
                "expense_type": extracted_data.get("expense_type")
            }
            expense_type_info = ExpenseTypeInfo(
                name="Meals with Client(s) - In Town",
                description="Business meals with clients while in town", 
                category="Meals & Entertainment"
            )
        
        elif "meals employee" in expense_type.lower():
            mapped_data = {
                "transaction_date": extracted_data.get("transaction_date"),
                "business_purpose": extracted_data.get("business_purpose"),
                "meal_type": extracted_data.get("meal_type"),
                "vendor": extracted_data.get("vendor"),
                "city": extracted_data.get("city"),
                "country": extracted_data.get("country", "US"),
                "payment_type": extracted_data.get("payment_type"),
                "amount": extracted_data.get("amount"),
                "currency": extracted_data.get("currency", "USD"),
                "attendees_count": extracted_data.get("attendees_count", 1),
                "comment": extracted_data.get("comment"),
                "expense_type": extracted_data.get("expense_type")
            }
            expense_type_info = ExpenseTypeInfo(
                name="Meals Employee(s) Only - In Town",
                description="Meals with only company employees while in town",
                category="Meals & Entertainment"
            )
        
        else:
            # Default mapping
            mapped_data = extracted_data
            expense_type_info = ExpenseTypeInfo(
                name=expense_type,
                description="Generic expense",
                category="Other"
            )
        
        # Validate the mapped data
        validation_errors = self.validate_expense_data_dict(mapped_data, expense_type)
        
        return MappingResult(mapped_data, expense_type_info, validation_errors)

    def validate_expense_data_dict(self, data: Dict[str, Any], expense_type: str) -> List[Dict[str, str]]:
        """Validate mapped expense data and return validation errors"""
        errors = []
        
        # Common validations
        if not data.get("transaction_date"):
            errors.append({"field": "transaction_date", "message": "Transaction date is required"})
        
        if not data.get("business_purpose"):
            errors.append({"field": "business_purpose", "message": "Business purpose is required"})
        
        if not data.get("vendor"):
            errors.append({"field": "vendor", "message": "Vendor is required"})
        
        if not data.get("amount") or data.get("amount", 0) <= 0:
            errors.append({"field": "amount", "message": "Valid amount is required"})
        
        # Expense type specific validations
        if "meals" in expense_type.lower():
            if not data.get("meal_type"):
                errors.append({"field": "meal_type", "message": "Meal type is required"})
            
            if "client" in expense_type.lower():
                if not data.get("client_prospect_name"):
                    errors.append({"field": "client_prospect_name", "message": "Client/Prospect name is required for client meals"})
                
                if not data.get("attendees_count") or data.get("attendees_count", 0) < 2:
                    errors.append({"field": "attendees_count", "message": "At least 2 attendees required for client meals"})
        
        elif "rideshare" in expense_type.lower() or "transportation" in expense_type.lower():
            if not data.get("starting_city"):
                errors.append({"field": "starting_city", "message": "Starting city is required for transportation"})
            
            if not data.get("travel_type"):
                errors.append({"field": "travel_type", "message": "Travel type is required"})
        
        return errors
    
    def get_expense_categories(self) -> List[str]:
        """Get all available expense categories"""
        return list(self.EXPENSE_TYPE_OPTIONS.keys())
    
    def get_expense_type_options(self, category: str) -> List[str]:
        """Get available expense types for a category"""
        return self.EXPENSE_TYPE_OPTIONS.get(category, [])

    def find_expense_type_id(self, expense_type_name: str) -> str:
        """Find expense type ID by name, with fuzzy matching"""
        if not expense_type_name:
            return ""  # Default fallback

        # Normalize the input
        normalized_name = expense_type_name.lower().strip()
        
        # Direct mapping lookup
        if normalized_name in self.EXPENSE_TYPE_MAPPING:
            return self.EXPENSE_TYPE_MAPPING[normalized_name]
        
        # Check aliases
        if normalized_name in self.EXPENSE_TYPE_ALIASES:
            return self.EXPENSE_TYPE_ALIASES[normalized_name]
        
        # Partial matching for common keywords
        for keyword, expense_id in self.EXPENSE_TYPE_ALIASES.items():
            if keyword in normalized_name:
                return expense_id
        
        # Default fallback
        return ""
    
    def find_payment_type_id(self, payment_type_name: str) -> str:
        """Find payment type ID by name, with fuzzy matching"""
        if not payment_type_name:
            return ""  # Default fallback

        # Normalize the input
        normalized_name = payment_type_name.lower().strip()
        
        # Direct mapping lookup
        if normalized_name in self.PAYMENT_TYPE_MAPPING:
            return self.PAYMENT_TYPE_MAPPING[normalized_name]
        
        # Default fallback
        return ""
    
    def get_expense_type_by_category_and_keywords(self, category: str, keywords: List[str]) -> str:
        """Get the most appropriate expense type based on category and keywords"""
        if not category or category not in self.EXPENSE_TYPE_OPTIONS:
            # Try to determine from keywords alone
            for keyword in keywords:
                expense_id = self.find_expense_type_id(keyword)
                if expense_id != "01028":  # If we found a specific match
                    return expense_id
            return "01028"
        
        # Get available types for the category
        available_types = self.EXPENSE_TYPE_OPTIONS[category]
        
        # Try to match keywords with available types
        for expense_type in available_types:
            expense_type_lower = expense_type.lower()
            for keyword in keywords:
                if keyword.lower() in expense_type_lower:
                    return self.find_expense_type_id(expense_type)
        
        # Return first available type in category if no keyword match
        if available_types:
            return self.find_expense_type_id(available_types[0])
        
        return "01028"
    
    def map_expense_data_to_entry(self, extracted_data, report_id: str) -> 'MappingResult':
        """Map enhanced expense data to SAP Concur expense entry format"""
        
        # Handle both dictionary and object input
        if isinstance(extracted_data, dict):
            # Convert dictionary access to dict.get() calls
            expense_type = extracted_data.get('expense_type')
            transaction_date = extracted_data.get('transaction_date')
            business_purpose = extracted_data.get('business_purpose')
            vendor = extracted_data.get('vendor')
            starting_city = extracted_data.get('starting_city')
            country = extracted_data.get('country')
            payment_type = extracted_data.get('payment_type')
            amount = extracted_data.get('amount')
            currency = extracted_data.get('currency')
            comment = extracted_data.get('comment')
            meal_type = extracted_data.get('meal_type')
        else:
            # Handle object attribute access
            expense_type = getattr(extracted_data, 'expense_type', None)
            transaction_date = getattr(extracted_data, 'transaction_date', None)
            business_purpose = getattr(extracted_data, 'business_purpose', None)
            vendor = getattr(extracted_data, 'vendor', None)
            starting_city = getattr(extracted_data, 'starting_city', None)
            country = getattr(extracted_data, 'country', None)
            payment_type = getattr(extracted_data, 'payment_type', None)
            amount = getattr(extracted_data, 'amount', None)
            currency = getattr(extracted_data, 'currency', None)
            comment = getattr(extracted_data, 'comment', None)
            meal_type = getattr(extracted_data, 'meal_type', None)

        print("******************Mapping expense data to entry in enhanced_expense_service.py:", extracted_data)
        print(f"Expense Type: {expense_type}")
        print(f"Transaction Date: {transaction_date}")
        print(f"Vendor: {vendor}")
        print(f"Amount: {amount}")
        print(f"Currency: {currency}")
        print(f"Business Purpose: {business_purpose}")
        print(f"Payment Type: {payment_type}")
        print(f"City: {starting_city}")
        print(f"Country: {country}")
        print(f"Comment: {comment}")
        print(f"Report ID: {report_id}")

        # Step 1 - Find the Expense Type Code
        expense_type_code = self.find_expense_type_id(expense_type)

        # Get payment type id
        payment_type_id = self.find_payment_type_id(payment_type)

        print(f"-----------------------------------------Expense Type Code: {expense_type_code}, Payment Type ID: {payment_type_id}")
        
        class MappingResult:
            def __init__(self, mapped_data, expense_type_info, validation_errors):
                self.mapped_data = mapped_data
                self.expense_type = expense_type_info
                self.validation_errors = validation_errors
        
        class ExpenseTypeInfo:
            def __init__(self, name, description, category):
                self.name = name
                self.description = description
                self.category = category
        
        # Map the data based on expense type
        if "rideshare" in expense_type.lower() or "uber" in expense_type.lower() or "lyft" in expense_type.lower():
            print("Mapping to Rideshare (Uber, Lyft) expense type")
            mapped_data = {
                "ReportID": report_id,
                "ExpenseTypeCode": expense_type_code,                
                "TransactionDate": transaction_date,
                "description": business_purpose,
                "fromLocation": starting_city,
                "paymentTypeId": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
                "TransactionAmount": amount,
                "TransactionCurrencyCode": currency,
                "VendorDescription": vendor,
                "custom9": "Client",
                "comment": comment,
                "expense_type": expense_type
            }
            print("------------------------- Mapped Data for Rideshare (Uber, Lyft):", mapped_data)
            expense_type_info = ExpenseTypeInfo(
                name="Rideshare (Uber, Lyft)",
                description="Rideshare transportation services",
                category="Transportation"
            )

        elif "meals with client" in expense_type.lower():
            mapped_data = {
                "ReportID": report_id,
                "ExpenseTypeCode": expense_type_code,
                "TransactionDate": transaction_date,
                "description": business_purpose,
                "meal_type": meal_type,
                "VendorDescription": vendor,
                "paymentTypeId": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
                "TransactionAmount": amount,
                "TransactionCurrencyCode": currency,
                "comment": comment,
                "expense_type": expense_type
            }
            expense_type_info = ExpenseTypeInfo(
                name="Meals with Client(s) - In Town",
                description="Business meals with clients while in town", 
                category="Meals & Entertainment"
            )

        elif "meals employee" in expense_type.lower():
            print("Mapping to Meals Employee(s) Only - In Town")
            mapped_data = {
                "ReportID": report_id,
                "ExpenseTypeCode": expense_type_code,
                "TransactionDate": transaction_date,
                "description": business_purpose,
                "meal_type": meal_type,
                "VendorDescription": vendor,
                "paymentTypeId": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
                "TransactionAmount": amount,
                "TransactionCurrencyCode": currency,
                "comment": comment,
                "expense_type": expense_type
            }
            expense_type_info = ExpenseTypeInfo(
                name="Meals Employee(s) Only - In Town",
                description="Meals with only company employees while in town",
                category="Meals & Entertainment"
            )
        
        else:
            # Default mapping
            mapped_data = {
                "ReportID": report_id,
                "ExpenseTypeCode": expense_type_code,
                "TransactionDate": transaction_date,
                "description": business_purpose,
                "VendorDescription": vendor,
                "paymentTypeId": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
                "TransactionAmount": amount,
                "TransactionCurrencyCode": currency,
                "comment": comment,
                "expense_type": expense_type
            }
            expense_type_info = ExpenseTypeInfo(
                name=expense_type,
                description="Generic expense",
                category="Other"
            )
        
        # Validate the mapped data
        validation_errors = {}

        return mapped_data










































        
        
        # # Get payment type ID - FIXED MAPPING
        # payment_type_key = (expense_data.payment_type or "personal credit card").lower()
        # payment_type_id = self._get_correct_payment_type_id(payment_type_key)
        
        # print(f"Payment Type ID: {payment_type_id}")
        
        # # Create description with business purpose
        # description = expense_data.business_purpose or "Business expense"
        # if len(description) > 64:
        #     description = description[:61] + "..."
        
        # # Vendor description
        # vendor_description = expense_data.vendor or "Unknown Vendor"
        # if len(vendor_description) > 64:
        #     vendor_description = vendor_description[:61] + "..."
        
        # # Handle location mapping - DYNAMIC BASED ON EXPENSE TYPE
        # if expense_type_code == "01072":  # Rideshare
        #     location_city = getattr(expense_data, 'starting_city', None) or expense_data.city or settings.DEFAULT_LOCATION_CITY
        # else:
        #     location_city = expense_data.city or settings.DEFAULT_LOCATION_CITY
            
        # location_country = expense_data.country or settings.DEFAULT_LOCATION_COUNTRY
        
        # return EnhancedExpenseEntryRequest(
        #     report_id=report_id,
        #     expense_type_code=expense_type_code,
        #     transaction_date=expense_data.transaction_date or datetime.now().strftime('%Y-%m-%d'),
        #     transaction_amount=expense_data.amount or 0.0,
        #     transaction_currency_code=expense_data.currency or "USD",
        #     payment_type_id=payment_type_id,
        #     description=description,
        #     vendor_description=vendor_description,
            
        #     # Meal-specific fields (only for meals)
        #     meal_type=getattr(expense_data, 'meal_type', None) if "meal" in expense_type_code.lower() or expense_type_code in ["01028", "01027", "01075", "01076"] else None,
        #     attendees_count=getattr(expense_data, 'attendees_count', None) if "meal" in expense_type_code.lower() or expense_type_code in ["01028", "01027", "01075", "01076"] else None,
        #     client_prospect_name=getattr(expense_data, 'client_prospect_name', None) if "meal" in expense_type_code.lower() or expense_type_code in ["01027", "01076"] else None,
            
        #     # Transportation-specific fields (only for transportation)
        #     travel_type=getattr(expense_data, 'travel_type', None) if expense_type_code == "01072" else None,
        #     starting_city=getattr(expense_data, 'starting_city', None) if expense_type_code == "01072" else None,
            
        #     # Location fields
        #     location_city=location_city,
        #     location_country=location_country,
        #     location_id=settings.DEFAULT_LOCATION_ID,
        #     location_name=settings.DEFAULT_LOCATION_NAME,
        #     location_country_subdivision=settings.DEFAULT_LOCATION_COUNTRY_SUBDIVISION
        # )
    
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
        
        # Validate expense type exists
        expense_type_id = self.find_expense_type_id(expense_data.expense_type)
        if expense_type_id == "01028" and expense_data.expense_type.lower() != "meals employee(s) only - in town":
            errors["expense_type"] = f"Expense type '{expense_data.expense_type}' not recognized"
        
        # Meal-specific validations
        if expense_data.expense_category == "04. Meals & Entertainment":
            if not expense_data.meal_type:
                errors["meal_type"] = "Meal type is required for meals"
            
            if expense_data.attendees_count and expense_data.attendees_count < 1:
                errors["attendees_count"] = "Attendees count must be at least 1"
            
            # Check if client/prospect name is needed
            if expense_data.expense_type and "client" in expense_data.expense_type.lower():
                if not expense_data.client_prospect_name:
                    errors["client_prospect_name"] = "Client/Prospect name is required for client meals"
        
        return errors
    
    def suggest_expense_category(self, description: str, vendor: str = "") -> str:
        """Suggest expense category based on description and vendor"""
        text = f"{description} {vendor}".lower()
        
        # Transportation keywords
        if any(word in text for word in ["uber", "lyft", "taxi", "rental", "gas", "parking", "toll", "train", "subway", "flight", "airfare"]):
            return "03. Transportation"
        
        # Lodging keywords  
        if any(word in text for word in ["hotel", "motel", "inn", "accommodation", "lodging"]):
            return "02. Lodging"
        
        # Meal keywords
        if any(word in text for word in ["restaurant", "meal", "lunch", "dinner", "breakfast", "food", "coffee", "catering"]):
            return "04. Meals & Entertainment"
        
        # Office keywords
        if any(word in text for word in ["office", "supplies", "software", "subscription", "postage", "print"]):
            return "10. Office Expense"
        
        # Default to office expense
        return "10. Office Expense"