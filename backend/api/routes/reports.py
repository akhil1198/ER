from fastapi import APIRouter, HTTPException
from models.report import ReportCreateRequest
from services import SAPService
from datetime import datetime

router = APIRouter(prefix="/api", tags=["reports"])

# Initialize services
sap_service = SAPService()

@router.get("/reports")
async def get_reports():
    """Get all expense reports"""
    try:
        reports = await sap_service.get_reports()
        return {
            "success": True,
            "reports": reports,
            "count": len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/formatted")
async def get_reports_formatted():
    """Get all expense reports with formatted message for chat"""
    try:
        reports = await sap_service.get_reports()
        if not reports:
            return {
                "success": True,
                "message": "📋 **No Reports Found**\n\nYou don't have any expense reports yet. Would you like to create one by uploading a receipt?",
                "reports": [],
                "count": 0
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
            "reports": reports,
            "count": len(reports)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@router.post("/reports")
async def create_report(report_data: ReportCreateRequest):
    """Create new expense report"""
    try:
        created_report = await sap_service.create_report(report_data)
        return {
            "success": True,
            "message": "Report created successfully!",
            "report": created_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
