import asyncio
import logging
from typing import Optional, Set
from pathlib import Path
from config.settings import settings
from src.engine.llm import chatbot_engine

logger = logging.getLogger(__name__)

class InstagramPrivateWorker:
    def __init__(self):
        self.username = settings.INSTAGRAM_USERNAME
        self.password = settings.INSTAGRAM_PASSWORD
        self.session_file = settings.INSTAGRAM_SESSION_FILE
        self.poll_interval = settings.INSTAGRAM_POLL_INTERVAL
        self.client = None
        self._processed_msg_ids: Set[str] = set()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def _login(self) -> bool:
        """Authenticates with Instagram using instagrapi and caches session."""
        if not self.username or not self.password:
            logger.info("INSTAGRAM_USERNAME or INSTAGRAM_PASSWORD not configured. Private API worker disabled.")
            return False

        try:
            from instagrapi import Client
            self.client = Client()

            # Attempt session reuse to prevent repeated login challenges
            if self.session_file.exists():
                try:
                    self.client.load_settings(self.session_file)
                    self.client.login(self.username, self.password)
                    logger.info("Successfully authenticated with cached Instagram session.")
                    return True
                except Exception as e:
                    logger.warning(f"Cached session invalid, re-authenticating: {e}")

            # Fresh login
            logger.info(f"Logging in to Instagram as @{self.username}...")
            self.client.login(self.username, self.password)
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(self.session_file)
            logger.info(f"Successfully logged in as @{self.username} and saved session.")
            return True

        except Exception as e:
            logger.error(f"Failed Instagram private API login: {e}")
            self.client = None
            return False

    async def _poll_loop(self):
        """Polls direct message threads and replies automatically."""
        while self._running:
            try:
                if self.client:
                    # Run synchronous instagrapi network calls in threadpool
                    threads = await asyncio.to_thread(self.client.direct_threads, 10)
                    my_user_id = str(self.client.user_id)

                    for thread in threads:
                        if not thread.messages:
                            continue

                        latest_msg = thread.messages[0]
                        msg_id = str(latest_msg.id)
                        sender_id = str(latest_msg.user_id)

                        # Skip our own outgoing messages or already processed messages
                        if sender_id == my_user_id or msg_id in self._processed_msg_ids:
                            continue

                        msg_text = latest_msg.text
                        if not msg_text:
                            continue

                        self._processed_msg_ids.add(msg_id)
                        # Keep processed set bounded
                        if len(self._processed_msg_ids) > 1000:
                            self._processed_msg_ids.clear()

                        logger.info(f"[Instagram Private Inbound] From: {sender_id} in thread {thread.id}: '{msg_text}'")

                        # Generate AI response
                        session_id = f"ig_private:{sender_id}"
                        bot_reply = await chatbot_engine.generate_response(session_id, msg_text)

                        # Send reply in thread
                        await asyncio.to_thread(
                            self.client.direct_send,
                            text=bot_reply,
                            thread_ids=[thread.id]
                        )
                        logger.info(f"[Instagram Private Outbound] Replied to thread {thread.id}")

            except Exception as e:
                logger.error(f"Error in Instagram private DM polling loop: {e}")

            await asyncio.sleep(self.poll_interval)

    def start(self):
        """Starts the background polling worker if credentials are set."""
        if not self.username or not self.password:
            return

        if self._login():
            self._running = True
            self._task = asyncio.create_task(self._poll_loop())
            logger.info("Instagram Private API worker started.")

    def stop(self):
        """Stops the polling loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Instagram Private API worker stopped.")

instagram_private_worker = InstagramPrivateWorker()
