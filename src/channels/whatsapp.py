import logging
import httpx
from typing import Optional, List, Dict, Any
from config.settings import settings
from src.schemas.models import InboundChatMessage

logger = logging.getLogger(__name__)

class WhatsAppChannel:
    def __init__(self):
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = settings.WHATSAPP_API_VERSION

    def parse_webhook_payload(self, payload: Dict[str, Any]) -> List[InboundChatMessage]:
        """Extracts text messages from a Meta WhatsApp Cloud API webhook event."""
        messages: List[InboundChatMessage] = []

        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    val = change.get("value", {})
                    if val.get("messaging_product") != "whatsapp":
                        continue

                    # Extract contact details
                    contacts = {c.get("wa_id"): c.get("profile", {}).get("name") for c in val.get("contacts", [])}

                    # Extract incoming messages
                    raw_msgs = val.get("messages", [])
                    for msg in raw_msgs:
                        if msg.get("type") == "text":
                            sender_id = msg.get("from")
                            text_body = msg.get("text", {}).get("body", "").strip()
                            if sender_id and text_body:
                                user_name = contacts.get(sender_id, "Customer")
                                messages.append(
                                    InboundChatMessage(
                                        channel="whatsapp",
                                        user_id=sender_id,
                                        user_name=user_name,
                                        message_text=text_body,
                                        message_id=msg.get("id"),
                                        raw_payload=msg
                                    )
                                )
        except Exception as e:
            logger.error(f"Failed to parse WhatsApp payload: {e}")

        return messages

    async def send_message(self, recipient_phone: str, text: str) -> bool:
        """Sends a text message reply via Meta WhatsApp Cloud API."""
        if not self.api_token or not self.phone_number_id:
            logger.warning(
                f"[WhatsApp Simulation] To: {recipient_phone} | Msg: {text[:60]}... (Configure WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env for live sending)"
            )
            return True

        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {"body": text}
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code in (200, 201):
                    logger.info(f"Successfully sent WhatsApp message to {recipient_phone}")
                    return True
                else:
                    logger.error(f"WhatsApp API Error {resp.status_code}: {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"Exception sending WhatsApp message: {e}")
                return False

whatsapp_channel = WhatsAppChannel()
