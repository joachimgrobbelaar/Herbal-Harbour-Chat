# Herbal-Harbour-Chat: 100% Free 24/7 Cloud Hosting & Client Setup Guide

This guide explains how to host **Herbal-Harbour-Chat** in the cloud 24/7 for **$0 / month (100% Free)** with zero paid services, and send the onboarding setup link to your client.

---

## 1. Zero-Cost Services Breakdown

- **AI Model**: Google Gemini API via [Google AI Studio](https://aistudio.google.com/) — **Free Tier** (15 requests/min, 1,500 requests/day, $0 forever, no credit card required).
- **Cloud Hosting**: [Render.com](https://render.com/) or [Koyeb.com](https://koyeb.com/) — **Free Tier Web Service** ($0 forever, automatic HTTPS URL).
- **Messaging Channels**: Baileys (WhatsApp Web QR) & instagrapi (Instagram Direct) — **$0** (zero Meta API billing or verification fees).

---

## 2. Deploying to 100% Free Cloud Hosting

### Option A: Render.com (100% Free - Recommended)
1. Push this directory to your GitHub account (public or private):
   ```bash
   cd /home/m/Projects/ai/herbal-harbour-bot
   git init && git add . && git commit -m "Initial commit"
   ```
2. Create a free account at [render.com](https://render.com/) (no credit card needed).
3. Click **New +** -> **Web Service**.
4. Select your GitHub repository.
5. In the service settings:
   - **Environment**: `Docker`
   - **Instance Type**: `Free` ($0/month)
   - **Port**: `8000`
6. Click **Create Web Service**.
7. Render will build the unified `Dockerfile` and give you a free permanent HTTPS address:
   `https://herbal-harbour-chat.onrender.com`

### Option B: Koyeb.com (100% Free)
1. Sign up at [koyeb.com](https://koyeb.com/) (free tier with Docker support).
2. Click **Create App** -> **GitHub**.
3. Select your repository, pick the **Nano Free** instance ($0/mo), and deploy.
4. Koyeb provides a free HTTPS domain: `https://<app-name>.koyeb.app`.

---

## 2. Sending the Onboarding Link to Your Client

Once deployed, copy your cloud URL and send your client the setup link:

> **Client Setup Link:**  
> `https://<YOUR-CLOUD-DOMAIN>/setup`  
> *(e.g., `https://herbal-harbour-production.up.railway.app/setup`)*

---

## 3. What the Client Does (Zero Technical Steps)

When the client opens the link on their phone or laptop:

### A. WhatsApp Connection
1. They see a live QR code on the webpage.
2. They open WhatsApp on their phone:
   - **iPhone**: Settings -> Linked Devices -> Link a Device
   - **Android**: Tap the 3 dots (top right) -> Linked Devices -> Link a Device
3. They scan the QR code displayed on the screen.
4. The webpage instantly turns green: **"WhatsApp Connected!"**. The bot is now live on their WhatsApp.

### B. Instagram Connection
1. In the **Instagram Direct** card on the same page, they type:
   - Instagram Username
   - Instagram Password
2. Click **Connect Instagram Account**.
3. The bot connects to their Instagram inbox and starts answering incoming DMs.

### C. Live Chat Simulator
They can click **Open Chat Preview** at the top right (`https://<YOUR-CLOUD-DOMAIN>/`) to test talking to the bot directly in their browser before live customers message them.
