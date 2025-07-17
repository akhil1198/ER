from .chat_service import ChatService
from .sap_service import SAPService
from .expense_service import ExpenseService
from .openai_service import OpenAIService

# Create singleton instances that will be shared across all routes
chat_service = ChatService()
sap_service = SAPService()
expense_service = ExpenseService()
openai_service = OpenAIService()