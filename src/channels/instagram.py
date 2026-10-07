import logging
import httpx
from typing import Optional, List, Dict, Any
from config.settings import settings
from src.schemas.models import InboundChatMessage

logger = logging.getLogger(__name__)

class InstagramChannel:
    def __init__(self):
        self.page_access_token = settings.INSTAGRAM_PAGE_ACCESS_TOKEN
        self.api_version = settings.INSTAGRAM_API_VERSION

    def parse_webhook_payload(self, payload: Dict[str, Any]) -> List[InboundChatMessage]:
        """Extracts direct text messages from an Instagram Messenger webhook event."""
        messages: List[InboundChatMessage] = []

        try:
            entries = payload.get("entry", [])
            for entry in entries:
                messaging_events = entry.get("messaging", [])
                for event in messaging_events:
                    sender_id = event.get("sender", {}).get("id")
                    msg = event.get("message", {})
                    # Skip echo messages sent by the bot/page itself
                    if msg.get("is_echo"):
                        continue

                    text_body = msg.get("text", "").strip()
                    if sender_id and text_body:
                        messages.append(
                            InboundChatMessage(
                                channel="instagram",
                                user_id=sender_id,
                                user_name=None,
                                message_text=text_body,
                                message_id=msg.get("mid"),
                                raw_payload=event
                            )
                        )
        except Exception as e:
            logger.error(f"Failed to parse Instagram payload: {e}")

        return messages

    async def send_message(self, recipient_id: str, text: str) -> bool:
        """Sends a text message reply via Instagram Messenger Graph API."""
        if not self.page_access_token:
            logger.warning(
                f"[Instagram Simulation] To: {recipient_id} | Msg: {text[:60]}... (Configure INSTAGRAM_PAGE_ACCESS_TOKEN in .env for live sending)"
            )
            return True

        url = f"https://graph.facebook.com/{self.api_version}/me/messages"
        headers = {
            "Authorization": f"Bearer {self.page_access_token}",
            "Content-Type": "application/json"
        }
        body = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code in (200, 201):
                    logger.info(f"Successfully sent Instagram message to {recipient_id}")
                    return True
                else:
                    logger.error(f"Instagram API Error {resp.status_code}: {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"Exception sending Instagram message: {e}")
                return False

instagram_channel = InstagramChannel()
