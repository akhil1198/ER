from .chat_service import ChatService
from .sap_service import SAPService
from .expense_service import ExpenseService  # Keep old service for legacy support
from .openai_service import OpenAIService    # Keep old service for legacy support

# Import new enhanced services
from .enhanced_expense_service import EnhancedExpenseService
from .enhanced_openai_service import EnhancedOpenAIService

# Create singleton instances that will be shared across all routes
chat_service = ChatService()
sap_service = SAPService()

# Legacy services (keep for backward compatibility)
expense_service = ExpenseService()
openai_service = OpenAIService()

# New enhanced services
enhanced_expense_service = EnhancedExpenseService()
enhanced_openai_service = EnhancedOpenAIService()