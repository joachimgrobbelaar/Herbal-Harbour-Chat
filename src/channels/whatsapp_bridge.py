import logging
import httpx
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppBridgeClient:
    def __init__(self, bridge_url: Optional[str] = None):
        self.bridge_url = bridge_url or settings.WHATSAPP_BRIDGE_URL

    async def is_connected(self) -> bool:
        """Checks if the Baileys WhatsApp QR bridge is active and paired."""
        status = await self.get_status()
        return status.get("connected", False)

    async def get_status(self) -> dict:
        """Gets pairing and connection status from the bridge."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.bridge_url}/status")
                if res.status_code == 200:
                    return res.json()
        except Exception:
            pass
        return {"connected": False, "hasQr": False, "user": None}

    async def get_qr_data(self) -> dict:
        """Retrieves the live base64 QR code data URL from the bridge."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.bridge_url}/qr-data")
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug(f"Could not fetch QR data from bridge: {e}")
        return {"connected": False, "qr": None}

    async def send_message(self, recipient_jid: str, text: str) -> bool:
        """Sends an outbound WhatsApp message via Baileys bridge."""
        url = f"{self.bridge_url}/send"
        payload = {"to": recipient_jid, "message": text}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info(f"Sent WhatsApp QR bridge message to {recipient_jid}")
                    return True
                else:
                    logger.error(f"WhatsApp bridge send error: {res.status_code} {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to communicate with WhatsApp bridge at {self.bridge_url}: {e}")
            return False

whatsapp_bridge = WhatsAppBridgeClient()
