from pydantic import BaseModel
from typing import Optional

class ReportCreateRequest(BaseModel):
    name: str
    business_purpose: str
    comment: Optional[str] = ""
    country_code: str = "US"
    country_subdivision_code: str = "US-WA"
    gift_policy_compliance: Optional[bool] = False
    irs_tax_policy_compliance: Optional[bool] = False