from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class InboundChatMessage(BaseModel):
    channel: str = Field(..., description="'whatsapp' or 'instagram'")
    user_id: str = Field(..., description="Phone number or Instagram user ID")
    user_name: Optional[str] = None
    message_text: str
    message_id: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None

class DirectChatRequest(BaseModel):
    user_id: str = "web_user"
    message: str
    channel: str = "direct"

class DirectChatResponse(BaseModel):
    reply: str
    channel: str
    user_id: str
