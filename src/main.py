import logging
import asyncio
from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from pathlib import Path

from config.settings import settings
from src.schemas.models import DirectChatRequest, DirectChatResponse, InboundChatMessage
from src.engine.llm import chatbot_engine
from src.channels.whatsapp import whatsapp_channel
from src.channels.instagram import instagram_channel
from src.channels.whatsapp_bridge import whatsapp_bridge
from src.channels.instagram_private import instagram_private_worker

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("herbal_harbour_bot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    instagram_private_worker.start()
    yield
    instagram_private_worker.stop()

app = FastAPI(
    title="Herbal-Harbour-Chat",
    description="Multi-channel AI Wellness Assistant for WhatsApp & Instagram",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "channels": ["whatsapp", "instagram"]
    }

@app.get("/api/channels/status")
async def get_channels_status():
    wa_status = await whatsapp_bridge.get_status()
    wa_user = wa_status.get("user") or {}

    ig_connected = bool(
        instagram_private_worker.client is not None and 
        instagram_private_worker._running
    )
    ig_username = settings.INSTAGRAM_USERNAME or None
    ig_chat_url = f"https://ig.me/m/{ig_username}" if ig_username else "https://www.instagram.com/herbalharbourroomservice420/"

    return {
        "status": "online",
        "whatsapp": {
            "connected": wa_status.get("connected", False),
            "phone": wa_user.get("phone"),
            "name": wa_user.get("name"),
            "chatUrl": wa_user.get("chatUrl") or (f"https://wa.me/{wa_user.get('phone')}" if wa_user.get('phone') else None)
        },
        "instagram": {
            "connected": ig_connected,
            "username": ig_username,
            "chatUrl": ig_chat_url,
            "profileUrl": f"https://www.instagram.com/{ig_username}/" if ig_username else "https://www.instagram.com/herbalharbourroomservice420/"
        },
        "portalUrl": "/setup"
    }

@app.get("/", response_class=HTMLResponse)
async def web_chat_ui():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Herbal-Harbour-Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-stone-100 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden flex flex-col h-[650px] border border-stone-200">
        <!-- Header -->
        <div id="chatHeader" class="bg-emerald-800 text-white p-4 flex items-center justify-between transition-colors">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center text-xl font-bold">🌿</div>
                <div>
                    <h1 class="font-semibold text-sm">Herbal-Harbour-Chat</h1>
                    <p id="channelBadge" class="text-xs text-emerald-200">Simulating: WhatsApp</p>
                </div>
            </div>
            <select id="channelSelect" class="bg-emerald-900 text-xs text-white rounded px-2 py-1 border border-emerald-700 outline-none">
                <option value="whatsapp">WhatsApp</option>
                <option value="instagram">Instagram</option>
            </select>
        </div>

        <!-- Chat messages area -->
        <div id="messages" class="flex-1 overflow-y-auto p-4 space-y-3 bg-[#efeae2]">
            <div class="bg-white p-3 rounded-lg shadow-sm max-w-[85%] text-xs leading-relaxed text-stone-800">
                🌿 <strong>Welcome to Herbal Harbour!</strong><br>
                How can I assist you with our organic teas, botanical tinctures, or remedies today?
            </div>
        </div>

        <!-- Input area -->
        <form id="chatForm" class="p-3 bg-stone-50 border-t border-stone-200 flex space-x-2">
            <input id="chatInput" type="text" placeholder="Ask about sleep tea, tinctures, shipping..." class="flex-1 text-sm border border-stone-300 rounded-full px-4 py-2 outline-none focus:ring-2 focus:ring-emerald-600" autocomplete="off" required>
            <button type="submit" class="bg-emerald-700 hover:bg-emerald-800 text-white text-sm px-4 py-2 rounded-full font-medium">Send</button>
        </form>
    </div>

    <script>
        const form = document.getElementById('chatForm');
        const input = document.getElementById('chatInput');
        const messages = document.getElementById('messages');
        const channelSelect = document.getElementById('channelSelect');
        const channelBadge = document.getElementById('channelBadge');
        const chatHeader = document.getElementById('chatHeader');

        channelSelect.addEventListener('change', () => {
            const isIg = channelSelect.value === 'instagram';
            channelBadge.textContent = isIg ? 'Simulating: Instagram Direct' : 'Simulating: WhatsApp';
            chatHeader.className = isIg 
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 flex items-center justify-between transition-colors'
                : 'bg-emerald-800 text-white p-4 flex items-center justify-between transition-colors';
            messages.style.backgroundColor = isIg ? '#fafafa' : '#efeae2';
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;
            input.value = '';

            // Render User bubble
            const userBubble = document.createElement('div');
            userBubble.className = 'ml-auto bg-emerald-600 text-white p-3 rounded-lg shadow-sm max-w-[85%] text-xs leading-relaxed';
            userBubble.textContent = text;
            messages.appendChild(userBubble);
            messages.scrollTop = messages.scrollHeight;

            // Typing indicator
            const typingBubble = document.createElement('div');
            typingBubble.className = 'bg-white p-3 rounded-lg shadow-sm max-w-[85%] text-xs text-stone-400 italic';
            typingBubble.textContent = 'Herbal Harbour is thinking...';
            messages.appendChild(typingBubble);
            messages.scrollTop = messages.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: 'web_visitor',
                        message: text,
                        channel: channelSelect.value
                    })
                });
                const data = await res.json();
                typingBubble.className = 'bg-white p-3 rounded-lg shadow-sm max-w-[85%] text-xs leading-relaxed text-stone-800 whitespace-pre-wrap';
                typingBubble.textContent = data.reply;
            } catch (err) {
                typingBubble.textContent = 'Error connecting to chatbot server.';
            }
            messages.scrollTop = messages.scrollHeight;
        });
    </script>
</body>
</html>"""

# =========================================================================
# META WEBHOOK VERIFICATION HELPER
# =========================================================================
def verify_meta_webhook(
    mode: Optional[str],
    token: Optional[str],
    challenge: Optional[str]
) -> Response:
    """Handles the Meta Graph API verification handshake (hub.mode, hub.verify_token)."""
    if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
        logger.info("Meta Webhook verification handshake succeeded.")
        return PlainTextResponse(content=challenge or "", status_code=200)
    logger.warning(f"Meta Webhook verification failed. Token mismatch or mode != subscribe. Mode: {mode}")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

# =========================================================================
# WHATSAPP CLOUD API WEBHOOKS
# =========================================================================
@app.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    return verify_meta_webhook(hub_mode, hub_verify_token, hub_challenge)

async def process_whatsapp_message(msg: InboundChatMessage):
    session_id = f"wa:{msg.user_id}"
    logger.info(f"Processing WhatsApp message from {msg.user_id}: '{msg.message_text}'")
    bot_reply = await chatbot_engine.generate_response(session_id, msg.message_text)
    await whatsapp_channel.send_message(msg.user_id, bot_reply)

@app.post("/webhook/whatsapp")
async def receive_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages = whatsapp_channel.parse_webhook_payload(payload)
    for msg in messages:
        background_tasks.add_task(process_whatsapp_message, msg)

    # Return 200 OK immediately to acknowledge receipt to Meta
    return {"status": "received", "count": len(messages)}

# =========================================================================
# INSTAGRAM MESSENGER API WEBHOOKS
# =========================================================================
@app.get("/webhook/instagram")
async def verify_instagram_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    return verify_meta_webhook(hub_mode, hub_verify_token, hub_challenge)

async def process_instagram_message(msg: InboundChatMessage):
    session_id = f"ig:{msg.user_id}"
    logger.info(f"Processing Instagram message from {msg.user_id}: '{msg.message_text}'")
    bot_reply = await chatbot_engine.generate_response(session_id, msg.message_text)
    await instagram_channel.send_message(msg.user_id, bot_reply)

@app.post("/webhook/instagram")
async def receive_instagram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages = instagram_channel.parse_webhook_payload(payload)
    for msg in messages:
        background_tasks.add_task(process_instagram_message, msg)

    return {"status": "received", "count": len(messages)}

# =========================================================================
# DIRECT TESTING API (Used for local interactive testing and web previews)
# =========================================================================
@app.post("/api/chat", response_model=DirectChatResponse)
async def direct_chat(req: DirectChatRequest):
    session_id = f"{req.channel}:{req.user_id}"
    reply = await chatbot_engine.generate_response(session_id, req.message)
    return DirectChatResponse(
        reply=reply,
        channel=req.channel,
        user_id=req.user_id
    )

# =========================================================================
# WHATSAPP QR BRIDGE ENDPOINT (Baileys integration)
# =========================================================================
@app.post("/api/bridge/whatsapp")
async def receive_whatsapp_bridge_message(req: DirectChatRequest):
    session_id = f"wa_qr:{req.user_id}"
    logger.info(f"Processing WhatsApp QR message from {req.user_id}: '{req.message}'")
    reply = await chatbot_engine.generate_response(session_id, req.message)
    return {
        "reply": reply,
        "user_id": req.user_id,
        "channel": "whatsapp_qr"
    }

# =========================================================================
# CLIENT ONBOARDING & SETUP PORTAL
# =========================================================================
@app.get("/setup", response_class=HTMLResponse)
async def client_setup_page():
    template_path = Path(__file__).resolve().parent / "templates" / "setup.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Setup template not found</h1>", status_code=404)

@app.get("/api/setup/whatsapp-status")
async def get_whatsapp_setup_status():
    data = await whatsapp_bridge.get_qr_data()
    return data

@app.post("/api/setup/instagram")
async def configure_instagram_credentials(payload: Dict[str, str]):
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()
    if not username or not password:
        return {"success": False, "message": "Username and password required"}

    # Update runtime settings
    settings.INSTAGRAM_USERNAME = username
    settings.INSTAGRAM_PASSWORD = password
    instagram_private_worker.username = username
    instagram_private_worker.password = password

    # Attempt login
    try:
        success = await asyncio.to_thread(instagram_private_worker._login)
        if success:
            instagram_private_worker.start()
            return {"success": True, "message": f"Successfully connected to @{username}"}
        else:
            return {"success": False, "message": "Authentication failed. Check credentials or 2FA challenge."}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/setup/gemini")
async def configure_gemini_api_key(payload: Dict[str, str]):
    key = payload.get("api_key", "").strip()
    if not key:
        return {"success": False, "message": "API key cannot be empty"}

    settings.GEMINI_API_KEY = key
    chatbot_engine.api_key = key
    chatbot_engine._init_client()
    return {"success": True, "message": "Gemini API key configured successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=True)
