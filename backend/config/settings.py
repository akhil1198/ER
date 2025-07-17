import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # SAP Concur Configuration
    SAP_BASE_URL: str = "https://us2.api.concursolutions.com"
    SAP_BEARER_TOKEN: Optional[str] = os.getenv("SAP_BEARER_TOKEN")
    SAP_USER_ID: str = "9e4f220f-b716-4738-9105-1153e04188ae"
    SAP_USER_LOGIN: str = "24FE8B14@GALLAGHER.uat"
    
    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Default Values
    DEFAULT_LOCATION_ID: str = "D23A4483615E4A2084260E97E5F0D5E0"
    DEFAULT_LOCATION_NAME: str = "Miami, Florida"
    DEFAULT_LOCATION_CITY: str = "Miami"
    DEFAULT_LOCATION_COUNTRY_SUBDIVISION: str = "US-FL"
    DEFAULT_LOCATION_COUNTRY: str = "US"
    DEFAULT_PAYMENT_TYPE_ID: str = "gWuT0oX4FNnukaeUcpOO3WSub$p5tY"
    DEFAULT_POLICY_ID: str = "2AFC92D1D0822F4A88D380BF14CFD05E"

settings = Settings()