from datetime import datetime
from typing import Dict, List
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
        
        # Default fallback
        "other": "01028"
    }
    
    PAYMENT_TYPE_MAPPING = {
        "cash": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "personal credit card": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY", 
        "corporate credit card": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "bank transfer": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY",
        "check": "gWuT0oX4FNnukaeUcpOO3WSub$p5tY"
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
    
    def get_expense_categories(self) -> List[str]:
        """Get all available expense categories"""
        return list(self.EXPENSE_TYPE_OPTIONS.keys())
    
    def get_expense_type_options(self, category: str) -> List[str]:
        """Get available expense types for a category"""
        return self.EXPENSE_TYPE_OPTIONS.get(category, ["Other"])
    
    def find_expense_type_id(self, expense_type_name: str) -> str:
        """Find expense type ID by name, with fuzzy matching"""
        if not expense_type_name:
            return "01028"  # Default fallback
            
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
        return "01028"
    
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
    
    def map_expense_data_to_entry(self, expense_data: EnhancedExpenseData, report_id: str) -> EnhancedExpenseEntryRequest:
        """Map enhanced expense data to SAP Concur expense entry format"""
        
        # Get expense type code with improved matching
        expense_type_code = self.find_expense_type_id(expense_data.expense_type)
        
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
            
            # Location fields
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