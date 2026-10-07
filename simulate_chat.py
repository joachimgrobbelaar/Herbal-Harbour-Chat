import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.engine.llm import chatbot_engine
from src.engine.session import session_manager

async def run_simulation():
    print("=" * 65)
    print("🌿 HERBAL HARBOUR AI CHATBOT - LOCAL SIMULATOR")
    print("=" * 65)
    print("Select simulated channel:")
    print("1) WhatsApp (wa:+15553472250)")
    print("2) Instagram Direct (ig:user_bot_tester)")
    
    choice = input("\nEnter choice [1 or 2, default: 1]: ").strip()
    if choice == "2":
        channel = "ig"
        user_id = "user_bot_tester"
        channel_name = "Instagram Direct"
    else:
        channel = "wa"
        user_id = "+15553472250"
        channel_name = "WhatsApp"

    session_id = f"{channel}:{user_id}"
    print(f"\n[Active Channel: {channel_name} | Session: {session_id}]")
    print("Type your message below (or type 'exit' or 'clear' to reset):")
    print("-" * 65)

    while True:
        try:
            user_msg = input("\nCustomer > ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ("exit", "quit", "q"):
                print("Exiting simulator. Goodbye!")
                break
            if user_msg.lower() == "clear":
                session_manager.clear_history(session_id)
                print("Session history cleared.")
                continue

            print("Bot is typing...\n")
            reply = await chatbot_engine.generate_response(session_id, user_msg)
            print(f"Herbal Harbour Bot >\n{reply}")
            print("-" * 65)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting simulator.")
            break

if __name__ == "__main__":
    asyncio.run(run_simulation())
