const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const QRCode = require('qrcode');
const pino = require('pino');
const express = require('express');
const axios = require('axios');
const path = require('path');

const PORT = process.env.WHATSAPP_BRIDGE_PORT || 3001;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000/api/bridge/whatsapp';
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');

let sock = null;
let isConnected = false;
let currentQrDataUrl = null;

const logger = pino({ level: 'warn' });

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        auth: state,
        logger,
        printQRInTerminal: false,
        browser: ['Herbal Harbour Bot', 'Desktop', '1.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n======================================================');
            console.log('🌿 SCAN THIS QR CODE WITH WHATSAPP TO CONNECT:');
            console.log('WhatsApp -> Settings / 3-dots -> Linked Devices -> Link Device');
            console.log('======================================================\n');
            qrcode.generate(qr, { small: true });
            QRCode.toDataURL(qr, { scale: 8, margin: 2 }, (err, url) => {
                if (!err) currentQrDataUrl = url;
            });
        }

        if (connection === 'close') {
            isConnected = false;
            const shouldReconnect =
                lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log(
                'WhatsApp connection closed due to:',
                lastDisconnect?.error?.message,
                'Reconnecting:',
                shouldReconnect
            );
            if (shouldReconnect) {
                setTimeout(connectToWhatsApp, 3000);
            } else {
                console.log('Logged out of WhatsApp. Delete auth_info_baileys to re-scan QR.');
            }
        } else if (connection === 'open') {
            isConnected = true;
            currentQrDataUrl = null;
            console.log('\n✅ [Herbal Harbour] WhatsApp Bridge Successfully Connected!\n');
        }
    });

    sock.ev.on('messages.upsert', async (m) => {
        try {
            if (m.type !== 'notify') return;

            for (const msg of m.messages) {
                // Ignore outgoing messages sent by the bot account itself
                if (msg.key.fromMe) continue;
                if (msg.key.remoteJid === 'status@broadcast') continue;

                const senderJid = msg.key.remoteJid;
                const pushName = msg.pushName || 'Customer';

                // Extract text message content
                const text =
                    msg.message?.conversation ||
                    msg.message?.extendedTextMessage?.text ||
                    msg.message?.imageMessage?.caption ||
                    '';

                if (!text || text.trim() === '') continue;

                console.log(`[WhatsApp Inbound] From: ${pushName} (${senderJid}) | Message: "${text}"`);

                // Send to FastAPI Chatbot Core
                try {
                    const response = await axios.post(FASTAPI_URL, {
                        user_id: senderJid,
                        user_name: pushName,
                        message: text,
                        channel: 'whatsapp_qr'
                    }, { timeout: 20000 });

                    const botReply = response.data?.reply;
                    if (botReply) {
                        await sock.sendMessage(senderJid, { text: botReply });
                        console.log(`[WhatsApp Outbound] Replied to ${senderJid}`);
                    }
                } catch (err) {
                    console.error('[WhatsApp Bridge] Error sending to FastAPI backend:', err.message);
                }
            }
        } catch (err) {
            console.error('[WhatsApp Bridge] messages.upsert handler error:', err);
        }
    });
}

// HTTP API for sending messages directly from FastAPI
const app = express();
app.use(express.json());

function getConnectedUser() {
    if (!isConnected || !sock || !sock.user) return null;
    const rawId = sock.user.id || '';
    const phone = rawId.split(':')[0].split('@')[0];
    return {
        id: rawId,
        phone: phone || null,
        name: sock.user.name || null,
        chatUrl: phone ? `https://wa.me/${phone}` : null
    };
}

app.get('/health', (req, res) => {
    res.json({ status: 'ok', connected: isConnected, user: getConnectedUser() });
});

app.get('/status', (req, res) => {
    res.json({ connected: isConnected, hasQr: !!currentQrDataUrl, user: getConnectedUser() });
});

app.get('/qr-data', (req, res) => {
    res.json({ connected: isConnected, qr: currentQrDataUrl, user: getConnectedUser() });
});

app.post('/send', async (req, res) => {
    const { to, message } = req.body;
    if (!to || !message) {
        return res.status(400).json({ error: 'Missing "to" or "message" field' });
    }
    if (!isConnected || !sock) {
        return res.status(503).json({ error: 'WhatsApp is not currently connected' });
    }

    try {
        await sock.sendMessage(to, { text: message });
        res.json({ success: true, to });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`WhatsApp Bridge HTTP API listening on port ${PORT}`);
    connectToWhatsApp();
});
