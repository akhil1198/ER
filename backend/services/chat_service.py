
import re
from typing import Optional, Dict, List, Any
from models.expense import ExpenseData

class ChatService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ChatService._initialized:
            # Initialize state only once
            self.conversation_state = "initial"
            self.current_expense_data: Optional[ExpenseData] = None
            self.available_reports: List[Dict] = []
            self.pending_report_data: Optional[Dict] = None
            self.pending_expense_data: Optional[ExpenseData] = None
            ChatService._initialized = True
            print("🏗️ ChatService singleton initialized")
    
    def update_conversation_state(self, state: str):
        """Update the conversation state"""
        print(f"🔄 State transition: {self.conversation_state} → {state}")
        self.conversation_state = state
    
    def set_current_expense(self, expense_data: ExpenseData):
        """Set current expense data"""
        self.current_expense_data = expense_data
        print(f"💰 Expense data set: {expense_data.vendor if expense_data else 'None'} - ${expense_data.amount if expense_data else 0}")
    
    def set_pending_expense(self, expense_data: ExpenseData):
        """Set pending expense data"""
        self.pending_expense_data = expense_data
        print(f"⏳ Pending expense data set: {expense_data.vendor if expense_data else 'None'}")
    
    def set_available_reports(self, reports: List[Dict]):
        """Set available reports"""
        self.available_reports = reports
        print(f"📋 Available reports set: {len(reports)} reports")
    
    def set_pending_report_data(self, report_data: Dict):
        """Set pending report data"""
        self.pending_report_data = report_data
        print(f"📊 Pending report data set: {report_data.get('name', 'Unknown')}")
    
    def clear_state(self):
        """Clear all conversation state"""
        print("🧹 Clearing all state")
        self.conversation_state = "initial"
        self.current_expense_data = None
        self.available_reports = []
        self.pending_report_data = None
        self.pending_expense_data = None
    
    def get_debug_info(self):
        """Get debug information about current state"""
        return {
            "conversation_state": self.conversation_state,
            "has_current_expense": bool(self.current_expense_data),
            "current_expense_vendor": self.current_expense_data.vendor if self.current_expense_data else None,
            "current_expense_amount": self.current_expense_data.amount if self.current_expense_data else None,
            "has_pending_expense": bool(self.pending_expense_data),
            "has_pending_report": bool(self.pending_report_data),
            "num_available_reports": len(self.available_reports),
            "instance_id": id(self)
        }
    
    def parse_report_details(self, message: str) -> Optional[Dict]:
        """Parse report details from user message with better flexibility"""
        
        # Try structured format first
        if ":" in message:
            lines = message.split('\n')
            report_name = ""
            business_purpose = ""
            comment = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if any(keyword in line.lower() for keyword in ["report name", "name"]) and ":" in line:
                    report_name = line.split(':', 1)[1].strip()
                elif any(keyword in line.lower() for keyword in ["business purpose", "purpose"]) and ":" in line:
                    business_purpose = line.split(':', 1)[1].strip()
                elif any(keyword in line.lower() for keyword in ["comment", "comments", "additional"]) and ":" in line:
                    comment = line.split(':', 1)[1].strip()
            
            if report_name and business_purpose:
                return {
                    "name": report_name,
                    "business_purpose": business_purpose,
                    "comment": comment or ""
                }
        
        # Try to extract from natural language
        message_lower = message.lower()
        
        # Look for common patterns
        name_patterns = [
            r"report.*?(?:name|called).*?[\"'](.*?)[\"']",
            r"name.*?[\"'](.*?)[\"']",
            r"call it [\"'](.*?)[\"']"
        ]
        
        purpose_patterns = [
            r"purpose.*?[\"'](.*?)[\"']",
            r"for [\"'](.*?)[\"']"
        ]
        
        extracted_name = ""
        extracted_purpose = ""
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted_name = match.group(1)
                break
        
        for pattern in purpose_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted_purpose = match.group(1)
                break
        
        if extracted_name and extracted_purpose:
            return {
                "name": extracted_name,
                "business_purpose": extracted_purpose,
                "comment": ""
            }
        
        return None
    
    def parse_tax_compliance_response(self, message: str) -> Optional[Dict]:
        """Parse tax compliance checkbox responses from user message"""
        message_lower = message.lower()
        
        # Initialize default values
        gift_policy = False
        irs_tax_policy = False
        
        # Look for positive indicators for gift policy compliance
        if any(phrase in message_lower for phrase in [
            "gift policy: true", "gift policy: yes", "gift policy compliance: true", 
            "gift policy compliance: yes", "gift: true", "gift: yes",
            "custom16: true", "custom16: yes", "first: true", "first: yes",
            "✓ gift", "checked gift", "agree gift", "accept gift"
        ]):
            gift_policy = True
        
        # Look for positive indicators for IRS tax policy compliance
        if any(phrase in message_lower for phrase in [
            "irs tax policy: true", "irs tax policy: yes", "irs: true", "irs: yes",
            "tax policy: true", "tax policy: yes", "custom6: true", "custom6: yes",
            "second: true", "second: yes", "✓ irs", "checked irs", "agree irs", "accept irs"
        ]):
            irs_tax_policy = True
        
        # Look for structured format with both checkboxes
        lines = message.split('\n')
        for line in lines:
            line = line.strip().lower()
            if 'gift' in line and ('true' in line or 'yes' in line or '✓' in line):
                gift_policy = True
            if 'irs' in line and ('true' in line or 'yes' in line or '✓' in line):
                irs_tax_policy = True
        
        return {
            "gift_policy_compliance": gift_policy,
            "irs_tax_policy_compliance": irs_tax_policy
        }