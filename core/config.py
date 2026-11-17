"""
LeadPulse AI - Core Configuration & Settings
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "leadpulse.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Application Branding
APP_NAME = "LeadPulse AI"
APP_TAGLINE = "Autonomous Lead Lifecycle & Business Development Platform"
APP_VERSION = "2.4.0-Enterprise"

# Default Integrations & API Keys (overridable via Environment or UI)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "109847291823901")
WHATSAPP_WABA_ID = os.environ.get("WHATSAPP_WABA_ID", "981273918239123")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "leadpulse_webhook_secure_token_2026")
WHATSAPP_API_VERSION = "v19.0"

# Scoring & Qualification Thresholds
LEAD_TEMP_HOT_THRESHOLD = 75
LEAD_TEMP_WARM_THRESHOLD = 45

# Verification Rules
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwawaymail.com", "yopmail.com", "sharklasers.com", "getairmail.com"
}
