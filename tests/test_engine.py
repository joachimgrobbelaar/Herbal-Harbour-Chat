import pytest
from src.engine.retriever import KnowledgeRetriever
from src.engine.session import SessionManager
from src.engine.llm import ChatbotEngine
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_retriever_product_matching():
    retriever = KnowledgeRetriever()
    results = retriever.search_products("sleep lavender", top_k=2)
    assert len(results) > 0
    assert any("Chamomile" in p["name"] for p in results)

def test_retriever_faq_matching():
    retriever = KnowledgeRetriever()
    faqs = retriever.search_faq("shipping delivery", top_k=1)
    assert len(faqs) == 1
    assert "shipping" in faqs[0]["question"].lower()

def test_session_manager():
    sm = SessionManager(max_history_per_session=3)
    sm.add_message("sess_1", "user", "Hi")
    sm.add_message("sess_1", "model", "Hello!")
    history = sm.get_history("sess_1")
    assert len(history) == 2
    assert history[0]["content"] == "Hi"
    assert history[1]["content"] == "Hello!"

    sm.clear_history("sess_1")
    assert len(sm.get_history("sess_1")) == 0

@pytest.mark.asyncio
async def test_chatbot_engine_fallback_generation():
    engine = ChatbotEngine()
    reply = await engine.generate_response("test-wa-user", "Do you have any herbal remedies for anxiety or sleep?")
    assert len(reply) > 20
    assert "Herbal Harbour" in reply

def test_direct_chat_api_endpoint():
    res = client.post(
        "/api/chat",
        json={
            "user_id": "test_direct_user",
            "message": "What time is your store open?",
            "channel": "direct"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert data["user_id"] == "test_direct_user"
