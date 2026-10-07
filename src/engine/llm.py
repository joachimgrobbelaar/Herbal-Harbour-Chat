import logging
from typing import Optional, List
from config.settings import settings
from src.engine.retriever import retriever
from src.engine.session import session_manager
from src.engine.prompts import SYSTEM_PROMPT, sanitize_commerce_language

logger = logging.getLogger(__name__)

class ChatbotEngine:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI client with model {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI client: {e}")
                self._client = None
        else:
            logger.warning("GEMINI_API_KEY is not set. Running in fallback simulation mode.")

    def _fallback_generate(self, user_message: str, grounding_context: str) -> str:
        """Rule-based smart fallback when GEMINI_API_KEY is not yet supplied."""
        matched_products = retriever.search_products(user_message, top_k=2)
        matched_faq = retriever.search_faq(user_message, top_k=1)

        reply_parts = ["🌿 **Welcome to Herbal Harbour!**"]
        reply_parts.append(
            "A designated percentage of every contribution funds our partner charitable initiatives — members support community causes and receive wellness gifts in reciprocity."
        )

        if matched_products:
            reply_parts.append("\nBased on what you're looking for, here are our recommended botanical gifts:")
            for p in matched_products:
                reply_parts.append(
                    f"\n• **{p['name']}** (suggested contribution ${p['price']:.2f})\n"
                    f"  ✨ *Benefits:* {', '.join(p['benefits'])}\n"
                    f"  🍵 *Suggested Use:* {p['directions']}"
                )
        elif matched_faq:
            f = matched_faq[0]
            reply_parts.append(f"\n**{f['question']}**\n{sanitize_commerce_language(f['answer'])}")
        else:
            reply_parts.append(
                "\nWe handcraft organic herbal teas, cognitive & calming tinctures, and therapeutic botanical salves.\n"
                "You can ask me about gifts for sleep, stress, energy, joint relief, Lion's Mane focus stacks, microdosing rhythms, the Canna-Spin-and-Win wheel, or WeeDeliver dispatch!"
            )

        reply_parts.append(
            "\n\n*⚠️ Disclaimer: Herbal Harbour botanical gifts support natural wellness and are not intended to diagnose, treat, or cure medical conditions. Consult your doctor if pregnant or on medications.*"
        )
        return sanitize_commerce_language("\n".join(reply_parts))

    async def generate_response(self, session_id: str, user_message: str) -> str:
        """Generates contextual AI response grounded in Herbal Harbour data."""
        # Retrieve grounding context
        grounding_context = retriever.get_grounding_context(user_message)
        
        # Record user message in session
        session_manager.add_message(session_id, role="user", content=user_message)
        history = session_manager.get_history(session_id)

        # If client is not available, use fallback
        if not self._client:
            reply = self._fallback_generate(user_message, grounding_context)
            session_manager.add_message(session_id, role="model", content=reply)
            return reply

        # Prepare prompt & history for Gemini
        try:
            from google.genai import types

            # Build conversational contents
            contents = []
            # We provide system instruction via config
            # Format multi-turn history
            for msg in history[:-1]:  # prior messages
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

            # Append current query with grounding context
            current_augmented_text = (
                f"[GROUNDING STORE CONTEXT]:\n{grounding_context}\n\n"
                f"[CUSTOMER MESSAGE]:\n{user_message}"
            )
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=current_augmented_text)]
                )
            )

            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=600
            )

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            bot_reply = response.text or "I'm sorry, I couldn't formulate a response. Please reach out to support@herbalharbour.com."
            bot_reply = sanitize_commerce_language(bot_reply)
            session_manager.add_message(session_id, role="model", content=bot_reply)
            return bot_reply

        except Exception as e:
            logger.error(f"Error during Gemini API generation: {e}")
            reply = self._fallback_generate(user_message, grounding_context)
            session_manager.add_message(session_id, role="model", content=reply)
            return reply

chatbot_engine = ChatbotEngine()
