from fastapi import APIRouter, HTTPException
from models.chat import ChatMessage
from models.expense import ExpenseData
from models.report import ReportCreateRequest
from services.shared_service import chat_service, sap_service, expense_service
from services.chat_service import ChatService
from services.sap_service import SAPService
from services.enhanced_expense_service import EnhancedExpenseService
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["chat"])

# Initialize services
chat_service = ChatService()
sap_service = SAPService()
expense_service = EnhancedExpenseService()

@router.post("/chat")
async def chat_endpoint(message: ChatMessage) -> Dict[str, Any]:
    """Handle chat messages and routing"""
    
    user_message = message.content.strip()
    print(f"User message: {user_message}, State: {chat_service.conversation_state}")
    
    try:
        # Handle different conversation states
        if chat_service.conversation_state == "waiting_for_choice":
            if user_message in ["1", "new", "create new", "create"]:
                chat_service.pending_expense_data = chat_service.current_expense_data
                chat_service.update_conversation_state("waiting_for_report_details")
                return {
                    "success": True,
                    "message": "Great! Let's create a new expense report.\n\nPlease provide the following information:\n\n**Report Name**: What should we call this report?\n**Business Purpose**: What's the purpose of this expense?\n\nYou can format it like this:\n```\nReport Name: July 2024 Office Supplies\nBusiness Purpose: Monthly office supplies purchase\n```\n\nOr just tell me in your own words!"
                }
            
            elif user_message in ["2", "existing", "add to existing"]:
                try:
                    reports = await sap_service.get_reports()
                    if not reports:
                        chat_service.update_conversation_state("waiting_for_choice")
                        return {
                            "success": True,
                            "message": "❌ No existing reports found. Would you like to create a new report instead?\n\nType **1** to create a new report."
                        }
                    
                    chat_service.set_available_reports(reports)
                    chat_service.update_conversation_state("waiting_for_report_selection")
                    
                    reports_text = "📋 **Here are your existing expense reports:**\n\n"
                    for i, report in enumerate(reports, 1):
                        status_emoji = "✅" if report['status'] == "Approved" else "⏳" if report['status'] == "Pending" else "📝"
                        reports_text += f"**{i}.** {status_emoji} **{report['name']}**\n"
                        reports_text += f"   • Purpose: {report['purpose'] or 'Not specified'}\n"
                        reports_text += f"   • Total: {report['total']} {report['currency']}\n"
                        reports_text += f"   • Status: {report['status']}\n\n"
                    
                    reports_text += "Please type the **number** of the report you'd like to add the expense to (e.g., type **3** for the third report)."
                    
                    return {
                        "success": True,
                        "message": reports_text
                    }
                    
                except Exception as e:
                    chat_service.update_conversation_state("waiting_for_choice")
                    return {
                        "success": False,
                        "message": f"❌ Failed to fetch reports: {str(e)}\n\nPlease try again or create a new report instead."
                    }
            
            else:
                return {
                    "success": False,
                    "message": "Please choose **1** for new report or **2** for existing report."
                }
        
        elif chat_service.conversation_state == "waiting_for_report_details":
            report_details = chat_service.parse_report_details(user_message)
            
            if report_details:
                chat_service.set_pending_report_data(report_details)
                chat_service.update_conversation_state("waiting_for_tax_compliance")
                
                return {
                    "success": True,
                    "message": "Perfect! I have your report details:\n\n📊 **Report Information:**\n• **Name**: {}\n• **Purpose**: {}\n\n🏛️ **Tax & Policy Compliance Required**\n\nBefore creating your expense report, you must agree to the following policies as required by IRS and company regulations:\n\n**Please confirm your agreement by checking both boxes below:**\n\n☐ **Gift Policy Compliance Certification** - I certify that this expense complies with company gift policy guidelines\n☐ **IRS T&E Tax Policy Certification** - I certify that this expense complies with IRS Travel & Entertainment tax policies\n\n**To proceed, please respond with:**\n```\nGift Policy Compliance: ✓\nIRS Tax Policy Compliance: ✓\n```\n\nOr simply type **\"I agree to both policies\"** if you accept both certifications.".format(
                        report_details['name'], 
                        report_details['business_purpose']
                    ),
                    "needs_tax_compliance": True
                }
            else:
                return {
                    "success": False,
                    "message": "I couldn't understand the report details. Please provide:\n\n**Report Name**: What should we call this report?\n**Business Purpose**: What's the purpose?\n\nExample:\n```\nReport Name: July Office Supplies\nBusiness Purpose: Monthly office supplies\n```"
                }
        
        elif chat_service.conversation_state == "waiting_for_tax_compliance":
            if any(phrase in user_message.lower() for phrase in [
                "i agree to both", "both policies", "agree to both", "accept both",
                "yes to both", "✓", "true", "agree", "accept", "yes"
            ]):
                if not chat_service.pending_report_data:
                    return {
                        "success": False,
                        "message": "❌ Session expired. Please start over by creating a new report."
                    }
                
                compliance_data = chat_service.parse_tax_compliance_response(user_message)
                
                if any(phrase in user_message.lower() for phrase in [
                    "i agree to both", "both policies", "agree to both", "accept both", "yes to both"
                ]):
                    compliance_data["gift_policy_compliance"] = True
                    compliance_data["irs_tax_policy_compliance"] = True
                
                if compliance_data and (compliance_data.get("gift_policy_compliance") or compliance_data.get("irs_tax_policy_compliance")):
                    try:
                        report_request = ReportCreateRequest(
                            name=chat_service.pending_report_data["name"],
                            business_purpose=chat_service.pending_report_data["business_purpose"],
                            comment=chat_service.pending_report_data.get("comment", ""),
                            gift_policy_compliance=compliance_data.get("gift_policy_compliance", False),
                            irs_tax_policy_compliance=compliance_data.get("irs_tax_policy_compliance", False)
                        )
                        
                        # Creating the report in SAP Concur
                        print(f"Creating report with data: {report_request}")
                        created_report = await sap_service.create_report(report_request)
                        
                        report_name = chat_service.pending_report_data["name"]
                        report_purpose = chat_service.pending_report_data["business_purpose"]
                        
                        # Extract the report ID
                        report_id = None
                        if isinstance(created_report, dict):
                            report_id = (created_report.get('reportId') or 
                                       created_report.get('ReportId') or 
                                       created_report.get('ID') or 
                                       created_report.get('Id'))
                        
                        # Try to add expense entry if we have both expense data and report ID
                        expense_added = False
                        expense_details = ""
                        
                        expense_data_to_use = chat_service.pending_expense_data or chat_service.current_expense_data
                        print("$$$$$$$$$$$$$$$$$$ expense_data_to_use:", expense_data_to_use)

                        if expense_data_to_use and report_id:
                            try:
                                expense_entry_data = expense_service.map_expense_data_to_entry(expense_data_to_use, report_id)
                                created_entry = await sap_service.create_expense_entry(expense_entry_data)
                                expense_added = True
                                
                                expense_details = f"\n\n💰 **Expense Added:**\n• **Vendor**: {expense_entry_data.vendor_description}\n• **Amount**: ${expense_entry_data.transaction_amount:.2f} {expense_entry_data.transaction_currency_code}\n• **Date**: {expense_entry_data.transaction_date}\n• **Description**: {expense_entry_data.description}"
                                
                            except Exception as e:
                                expense_details = f"\n\n⚠️ **Note**: Report created successfully, but there was an issue adding the expense entry: {str(e)}\nYou can manually add the expense in SAP Concur."
                        
                        # Clear state
                        chat_service.clear_state()
                        
                        compliance_status = []
                        if compliance_data.get("gift_policy_compliance"):
                            compliance_status.append("✅ Gift Policy Compliance")
                        else:
                            compliance_status.append("❌ Gift Policy Compliance")
                        
                        if compliance_data.get("irs_tax_policy_compliance"):
                            compliance_status.append("✅ IRS T&E Tax Policy Compliance")
                        else:
                            compliance_status.append("❌ IRS T&E Tax Policy Compliance")
                        
                        success_message = f"✅ **Report created successfully!**\n\n📊 **Report Details:**\n• **Name**: {report_name}\n• **Purpose**: {report_purpose}\n• **Report ID**: {report_id or 'N/A'}\n\n🏛️ **Policy Compliance Status:**\n{chr(10).join(compliance_status)}{expense_details}\n\n🎉 {'Your expense report is complete with the expense entry!' if expense_added else 'Your expense report is ready for expenses!'}"
                        
                        return {
                            "success": True,
                            "message": success_message
                        }
                        
                    except Exception as e:
                        chat_service.clear_state()
                        return {
                            "success": False,
                            "message": f"❌ Failed to create report: {str(e)}\n\nPlease try again with the compliance confirmations."
                        }
                else:
                    return {
                        "success": False,
                        "message": "⚠️ **Policy Compliance Required**\n\nYou must agree to at least one of the policy certifications to create an expense report. Please confirm:\n\n☐ **Gift Policy Compliance Certification**\n☐ **IRS T&E Tax Policy Certification**\n\nType **\"I agree to both policies\"** or confirm each policy individually."
                    }
            else:
                return {
                    "success": False,
                    "message": "🏛️ **Policy Compliance Required**\n\nPlease confirm your agreement to the required policies:\n\n☐ **Gift Policy Compliance Certification**\n☐ **IRS T&E Tax Policy Certification**\n\nRespond with:\n```\nGift Policy Compliance: ✓\nIRS Tax Policy Compliance: ✓\n```\n\nOr type **\"I agree to both policies\"** to accept both."
                }
        
        elif chat_service.conversation_state == "waiting_for_report_selection":
            try:
                selection = int(user_message)
                if 1 <= selection <= len(chat_service.available_reports):
                    selected_report = chat_service.available_reports[selection - 1]
                    
                    if chat_service.current_expense_data:
                        print("#####################################current_expense_data being sent to map_expense_data_to_entry:", chat_service.current_expense_data)
                        try:

                            expense_entry_data = expense_service.map_expense_data_to_entry(chat_service.current_expense_data, selected_report['id'])
                            print("#####################################expense_entry_data being sent to create_expense_entry:", expense_entry_data)
                            created_entry = await sap_service.create_expense_entry(expense_entry_data)
                            print("%%%%%%%%%%%%%%%%%%%%%%%% created_entry:", created_entry)
                            print("asdfasdfasdfasdfasdf")
                            chat_service.clear_state()
                            
                            return {
                                "success": True,
                                "message": f"✅ **Expense added successfully!**\n\n📊 **Report Details:**\n• **Report**: {selected_report['name']}\n• **Previous Total**: {selected_report['total']} {selected_report['currency']}\n• **New Expense**: ${expense_entry_data.get('TransactionAmount', 0):.2f}\n• **Status**: {selected_report['status']}\n\n💰 **Expense Details:**\n• **Vendor**: {expense_entry_data.get('VendorDescription', 'Unknown')}\n• **Amount**: ${expense_entry_data.get('TransactionAmount', 0):.2f} {expense_entry_data.get('TransactionCurrencyCode', 'USD')}\n• **Date**: {expense_entry_data.get('TransactionDate', 'Unknown')}\n• **Description**: {expense_entry_data.get('description', 'No description')}\n\n🎉 Your expense has been successfully added to the report!"
                            }
                            
                        except Exception as e:
                            chat_service.clear_state()
                            return {
                                "success": False,
                                "message": f"❌ There was an issue adding the expense entry to SAP Concur: {str(e)}\n\nThe report selection was successful, but you may need to manually add the expense details in SAP Concur."
                            }
                    else:
                        chat_service.clear_state()
                        return {
                            "success": True,
                            "message": f"✅ **Report selected!**\n\n📊 **Selected Report:**\n• Name: {selected_report['name']}\n• Purpose: {selected_report['purpose']}\n• Current Total: {selected_report['total']} {selected_report['currency']}\n• Status: {selected_report['status']}\n\n🎉 Your report is ready for expenses!"
                        }
                else:
                    return {
                        "success": False,
                        "message": f"❌ Invalid selection. Please choose a number between 1 and {len(chat_service.available_reports)}."
                    }
                    
            except ValueError:
                return {
                    "success": False,
                    "message": "❌ Please enter a valid number to select a report."
                }
        
        else:  # initial state
            # Check for report fetching commands
            if any(phrase in user_message.lower() for phrase in [
                "show reports", "list reports", "get reports", "fetch reports", 
                "view reports", "my reports", "existing reports", "all reports",
                "show my reports", "list my reports"
            ]):
                try:
                    reports = await sap_service.get_reports()
                    if not reports:
                        return {
                            "success": True,
                            "message": "📋 **No Reports Found**\n\nYou don't have any expense reports yet. Would you like to create one by uploading a receipt?"
                        }
                    
                    reports_text = f"📋 **Your Expense Reports** ({len(reports)} found)\n\n"
                    
                    for i, report in enumerate(reports, 1):
                        status_emoji = {
                            "Approved": "✅",
                            "Submitted": "📤", 
                            "Pending Approval": "⏳",
                            "Draft": "📝",
                            "Rejected": "❌"
                        }.get(report['status'], "📄")
                        
                        created_date = "Unknown"
                        if report.get('created'):
                            try:
                                from datetime import datetime
                                created_date = datetime.fromisoformat(report['created'].replace('T', ' ').replace('Z', '')).strftime('%m/%d/%Y')
                            except:
                                created_date = report['created'][:10] if len(report['created']) >= 10 else "Unknown"
                        
                        reports_text += f"**{i}.** {status_emoji} **{report['name']}**\n"
                        reports_text += f"   • Purpose: {report['purpose'] or 'Not specified'}\n"
                        reports_text += f"   • Amount: {report['total']} {report['currency']}\n"
                        reports_text += f"   • Status: {report['status']}\n"
                        reports_text += f"   • Created: {created_date}\n"
                        reports_text += f"   • ID: {report['id']}\n\n"
                    
                    reports_text += "💡 **Want to add an expense?** Upload a receipt and I'll help you add it to one of these reports!"
                    
                    return {
                        "success": True,
                        "message": reports_text,
                        "reports": reports
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"❌ **Failed to fetch reports**\n\nError: {str(e)}\n\nPlease check your SAP Concur connection and try again."
                    }
            
            # Check for help commands
            elif any(phrase in user_message.lower() for phrase in [
                "help", "what can you do", "commands", "options"
            ]):
                return {
                    "success": True,
                    "message": "🤖 **Here's what I can help you with:**\n\n📷 **Upload Receipt**: Drag & drop or click 📎 to upload a receipt image\n📋 **View Reports**: Type 'show my reports' to see all your expense reports\n➕ **Create Report**: Upload a receipt and I'll help you create a new report\n🔗 **Add to Existing**: Upload a receipt and add it to an existing report\n\n💡 **Quick Commands:**\n• `show reports` - View all your reports\n• `help` - Show this help message\n\nJust upload a receipt to get started!"
                }
            
            # Default responses
            elif chat_service.current_expense_data:
                chat_service.update_conversation_state("waiting_for_choice")
                return {
                    "success": True,
                    "message": "I have your expense data ready! What would you like to do?\n\n**1** - Create a new expense report\n**2** - Add to an existing report\n\nType **1** or **2** to continue!",
                    "expense_data": chat_service.current_expense_data.dict()
                }
            else:
                return {
                    "success": True,
                    "message": "👋 **Welcome to the Expense Assistant!**\n\nI'm here to help you streamline your expense reporting process. Here's what I can do for you:\n\n• **📷 Upload receipts** - Just drag & drop or click the attachment button, and I'll automatically extract all the expense details\n• **📋 Manage reports** - Type 'show reports' to view your existing expense reports\n• **💬 Get help** - Type 'help' to see all available commands\n\nReady to get started? Upload a receipt or ask me anything!"
                }
    
    except Exception as e:
        print(f"Chat error: {str(e)}")
        chat_service.clear_state()
        return {
            "success": False,
            "message": f"❌ Something went wrong: {str(e)}\n\nPlease try again or upload a new receipt to start over."
        }