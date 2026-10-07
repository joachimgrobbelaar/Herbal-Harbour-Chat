# Herbal-Harbour-Chat

An AI-powered customer service assistant for **Herbal Harbour**, designed to automatically respond to customer inquiries on **WhatsApp** and **Instagram Direct**, grounded in official product catalog data and botanical safety guidelines.

---

## Features

- **Multi-Channel Support**: Seamless webhook processing and messaging dispatch for both Meta WhatsApp Cloud API and Instagram Messenger (Graph API).
- **Domain Grounding**: Catalog lookup for teas, tinctures, elixirs, and salves (`data/products.json`) plus store policies and FAQs (`data/business_faq.json`).
- **Medical & Botanical Safety Guardrails**: Enforces non-clinical wellness boundaries with automated disclaimer notices for pregnancy, prescription medications, or serious health queries.
- **Conversational Session Memory**: Sliding-window context tracking per user across multi-turn chats.
- **Local Interactive Simulator**: Terminal test harness (`simulate_chat.py`) to test conversation flows without requiring live Meta webhooks.
- **Graceful Fallbacks**: Works out of the box with offline grounding even before adding live API credentials.

---

## Directory Structure

```
herbal-harbour-bot/
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration & Pydantic settings
├── data/
│   ├── products.json            # Herbal Harbour products catalog
│   └── business_faq.json        # FAQs, business hours, and store policies
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── whatsapp.py          # WhatsApp Cloud API handler
│   │   └── instagram.py         # Instagram Messenger Graph API handler
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── llm.py               # Google GenAI (Gemini) chat engine
│   │   ├── prompts.py           # Herbal Harbour persona & safety guardrails
│   │   ├── retriever.py         # Catalog & FAQ keyword retriever
│   │   └── session.py           # Per-user conversation memory
│   └── schemas/
│       ├── __init__.py
│       └── models.py            # Inbound/outbound message data models
├── tests/
│   ├── test_engine.py           # Engine & retrieval unit tests
│   └── test_webhooks.py         # Meta webhook verification & payload tests
├── simulate_chat.py             # CLI simulation harness
├── requirements.txt
├── pytest.ini
├── Dockerfile
└── .env.example
```

---

## Getting Started

### 1. Environment Setup

```bash
cd /home/m/Projects/ai/herbal-harbour-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to configure your API keys:
- `GEMINI_API_KEY`: Google AI Studio API key
- `META_VERIFY_TOKEN`: Webhook verification secret token
- `WHATSAPP_API_TOKEN` & `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp Cloud API credentials
- `INSTAGRAM_PAGE_ACCESS_TOKEN`: Instagram Graph API token

---

## Option A: WhatsApp QR Bridge & Instagram Private API (No Meta Account)

### 1. WhatsApp QR Code Pairing (Baileys)
Connect any personal or business WhatsApp number by scanning a QR code in the terminal:

```bash
# Start the WhatsApp QR bridge
./run_bot.sh wa-bridge
```
1. A QR code will display in the terminal.
2. Open WhatsApp on your phone -> **Settings** (or 3-dots) -> **Linked Devices** -> **Link a Device**.
3. Scan the QR code. The session is cached in `bridges/whatsapp/auth_info_baileys/` so you only scan once.

### 2. Instagram Private Web API (`instagrapi`)
Add your Instagram username and password to `.env`:
```env
INSTAGRAM_USERNAME=your_bot_instagram_account
INSTAGRAM_PASSWORD=your_instagram_password
```
When FastAPI starts, it automatically logs in, caches the session in `data/ig_session.json` to prevent re-verification challenges, and polls for unread DMs.

### 3. Run Both Services Together
```bash
./run_bot.sh all
```

---

## Option B: Local Interactive Simulation (Offline)

To test conversation flows and product recommendations immediately in your terminal:

```bash
python3 simulate_chat.py
```

Choose channel (WhatsApp or Instagram) and chat interactively.

---

## Running the Webhook Server

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints exposed:
- `GET /health`: Health status check
- `GET /webhook/whatsapp` & `POST /webhook/whatsapp`: WhatsApp Cloud API webhook
- `GET /webhook/instagram` & `POST /webhook/instagram`: Instagram Graph API webhook
- `POST /api/chat`: Direct REST testing endpoint

---

## Meta Developer Setup Guide

### WhatsApp Cloud API
1. Go to [Meta for Developers](https://developers.facebook.com/) and create a Business App.
2. Add the **WhatsApp** product.
3. In **Configuration** -> **Webhooks**:
   - Callback URL: `https://<your-public-domain>/webhook/whatsapp`
   - Verify Token: value matching `META_VERIFY_TOKEN` in `.env`.
   - Subscribe to the `messages` webhook field.
4. Copy the **Phone number ID** and **Access Token** into `.env`.

### Instagram Direct Messaging
1. In your Meta App, add **Instagram Graph API** / **Messenger**.
2. Connect your Instagram Professional/Creator account to a Facebook Page.
3. In **Webhooks**:
   - Select **Instagram**.
   - Callback URL: `https://<your-public-domain>/webhook/instagram`
   - Verify Token: value matching `META_VERIFY_TOKEN` in `.env`.
   - Subscribe to `messages`.
4. Generate a Page Access Token with `instagram_manage_messages` permission and paste it into `.env`.

---

## Running Automated Tests

```bash
pytest
```
