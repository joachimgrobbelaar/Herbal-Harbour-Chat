import pytest
from fastapi.testclient import TestClient
from config.settings import settings
from src.main import app
from src.channels.whatsapp import whatsapp_channel
from src.channels.instagram import instagram_channel

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "whatsapp" in data["channels"]
    assert "instagram" in data["channels"]

def test_whatsapp_webhook_verification():
    # Valid verification
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.META_VERIFY_TOKEN,
            "hub.challenge": "1153257786"
        }
    )
    assert response.status_code == 200
    assert response.text == "1153257786"

    # Invalid token verification
    response_bad = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_secret_token",
            "hub.challenge": "1153257786"
        }
    )
    assert response_bad.status_code == 403

def test_instagram_webhook_verification():
    # Valid verification
    response = client.get(
        "/webhook/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.META_VERIFY_TOKEN,
            "hub.challenge": "9988776655"
        }
    )
    assert response.status_code == 200
    assert response.text == "9988776655"

def test_whatsapp_payload_parsing():
    sample_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID_123",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": "PHONE_ID_123"
                    },
                    "contacts": [{
                        "profile": {"name": "Alice Green"},
                        "wa_id": "16315550099"
                    }],
                    "messages": [{
                        "from": "16315550099",
                        "id": "wamid.HBgLMTYzMTU1NTAwOTkVAgASGBQz",
                        "timestamp": "1728284400",
                        "text": {"body": "Do you have any soothing teas for anxiety?"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    parsed = whatsapp_channel.parse_webhook_payload(sample_payload)
    assert len(parsed) == 1
    assert parsed[0].channel == "whatsapp"
    assert parsed[0].user_id == "16315550099"
    assert parsed[0].user_name == "Alice Green"
    assert "soothing teas for anxiety" in parsed[0].message_text

def test_instagram_payload_parsing():
    sample_payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID_987",
            "time": 1728284400,
            "messaging": [{
                "sender": {"id": "ig_user_4455"},
                "recipient": {"id": "PAGE_ID_987"},
                "timestamp": 1728284400,
                "message": {
                    "mid": "mid.123456",
                    "text": "What are your shipping rates?"
                }
            }]
        }]
    }

    parsed = instagram_channel.parse_webhook_payload(sample_payload)
    assert len(parsed) == 1
    assert parsed[0].channel == "instagram"
    assert parsed[0].user_id == "ig_user_4455"
    assert "shipping rates" in parsed[0].message_text

def test_whatsapp_post_webhook_endpoint():
    sample_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID_123",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "contacts": [{"profile": {"name": "Bob"}, "wa_id": "15551112222"}],
                    "messages": [{
                        "from": "15551112222",
                        "id": "wamid.123",
                        "text": {"body": "Hello"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    res = client.post("/webhook/whatsapp", json=sample_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "received"

def test_whatsapp_bridge_endpoint():
    res = client.post(
        "/api/bridge/whatsapp",
        json={
            "user_id": "15559876543@s.whatsapp.net",
            "message": "Do you sell any natural teas for deep sleep?",
            "channel": "whatsapp_qr"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert data["channel"] == "whatsapp_qr"
    assert data["user_id"] == "15559876543@s.whatsapp.net"

def test_client_setup_portal():
    res = client.get("/setup")
    assert res.status_code == 200
    assert "Herbal-Harbour-Chat" in res.text
    assert "WhatsApp Web" in res.text

def test_api_setup_whatsapp_status():
    res = client.get("/api/setup/whatsapp-status")
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data

def test_channels_status_endpoint():
    res = client.get("/api/channels/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "whatsapp" in data
    assert "instagram" in data
    assert "portalUrl" in data
