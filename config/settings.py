from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Herbal-Harbour-Chat"
    ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Meta Webhook Verification
    META_VERIFY_TOKEN: str = "herbal_harbour_verify_secret_token"
    META_APP_SECRET: Optional[str] = None

    # WhatsApp Cloud API Configuration
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_API_VERSION: str = "v21.0"

    # Instagram Graph API Configuration
    INSTAGRAM_PAGE_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_PAGE_ID: Optional[str] = None
    INSTAGRAM_API_VERSION: str = "v21.0"

    # WhatsApp QR Bridge (Baileys) Configuration
    WHATSAPP_BRIDGE_URL: str = "http://localhost:3001"
    WHATSAPP_BRIDGE_PORT: int = 3001

    # Instagram Private Web API (instagrapi) Configuration
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    INSTAGRAM_SESSION_FILE: Path = BASE_DIR / "data" / "ig_session.json"
    INSTAGRAM_POLL_INTERVAL: int = 10

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Data paths
    PRODUCTS_FILE: Path = BASE_DIR / "data" / "products.json"
    FAQ_FILE: Path = BASE_DIR / "data" / "business_faq.json"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
