(function() {
  // Prevent duplicate injection
  if (window.__HerbalHarbourWidgetLoaded) return;
  window.__HerbalHarbourWidgetLoaded = true;

  // Resolve API Base URL from the script tag source
  let scriptTag = document.currentScript;
  if (!scriptTag) {
    const scripts = document.getElementsByTagName('script');
    for (let s of scripts) {
      if (s.src && s.src.includes('widget.js')) {
        scriptTag = s;
        break;
      }
    }
  }

  let baseUrl = '';
  if (scriptTag && scriptTag.src) {
    try {
      const u = new URL(scriptTag.src);
      baseUrl = u.origin;
    } catch (e) {
      baseUrl = window.location.origin;
    }
  } else {
    baseUrl = window.location.origin;
  }

  // Session ID for web visitor
  let visitorId = localStorage.getItem('hh_chat_visitor_id');
  if (!visitorId) {
    visitorId = 'web_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('hh_chat_visitor_id', visitorId);
  }

  // Inject Styles
  const style = document.createElement('style');
  style.id = 'hh-widget-styles';
  style.textContent = `
    #hh-widget-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    #hh-widget-toggle {
      width: 58px;
      height: 58px;
      border-radius: 50%;
      background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
      box-shadow: 0 8px 24px rgba(6, 78, 59, 0.35);
      border: 2px solid #a7f3d0;
      color: #ffffff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      outline: none;
    }
    #hh-widget-toggle:hover {
      transform: scale(1.05);
      box-shadow: 0 10px 28px rgba(6, 78, 59, 0.45);
    }
    #hh-widget-window {
      display: none;
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 375px;
      max-width: calc(100vw - 32px);
      height: 540px;
      max-height: calc(100vh - 120px);
      background: #fdfbf7;
      border-radius: 18px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
      border: 1px solid #e7e2d9;
      flex-direction: column;
      overflow: hidden;
      z-index: 2147483647;
    }
    #hh-widget-window.hh-open {
      display: flex;
      animation: hh-slideup 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes hh-slideup {
      from { opacity: 0; transform: translateY(16px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .hh-header {
      background: #064e3b;
      color: #ffffff;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 2px solid #047857;
    }
    .hh-header-title {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .hh-header-status {
      font-size: 11px;
      color: #a7f3d0;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .hh-header-status::before {
      content: '';
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #34d399;
      box-shadow: 0 0 6px #34d399;
    }
    .hh-close-btn {
      background: transparent;
      border: none;
      color: #a7f3d0;
      font-size: 20px;
      cursor: pointer;
      line-height: 1;
      padding: 4px;
    }
    .hh-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #faf7f2;
    }
    .hh-msg {
      max-width: 82%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 13.5px;
      line-height: 1.45;
      word-wrap: break-word;
      white-space: pre-wrap;
    }
    .hh-msg.bot {
      align-self: flex-start;
      background: #ffffff;
      color: #27272a;
      border: 1px solid #e4e4e7;
      border-bottom-left-radius: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .hh-msg.user {
      align-self: flex-end;
      background: #064e3b;
      color: #ffffff;
      border-bottom-right-radius: 4px;
      box-shadow: 0 1px 3px rgba(6,78,59,0.2);
    }
    .hh-suggestions {
      padding: 8px 14px;
      display: flex;
      gap: 6px;
      overflow-x: auto;
      background: #faf7f2;
      border-top: 1px solid #eee8df;
    }
    .hh-chip {
      background: #ffffff;
      border: 1px solid #d1d5db;
      border-radius: 14px;
      padding: 4px 10px;
      font-size: 11.5px;
      color: #064e3b;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
    }
    .hh-chip:hover {
      background: #ecfdf5;
      border-color: #059669;
    }
    .hh-input-bar {
      padding: 10px 14px;
      background: #ffffff;
      border-top: 1px solid #e7e2d9;
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .hh-input-bar input {
      flex: 1;
      border: 1px solid #d4d4d8;
      border-radius: 20px;
      padding: 8px 14px;
      font-size: 13px;
      outline: none;
      background: #fafafa;
    }
    .hh-input-bar input:focus {
      border-color: #059669;
      background: #ffffff;
    }
    .hh-send-btn {
      background: #064e3b;
      color: white;
      border: none;
      border-radius: 50%;
      width: 34px;
      height: 34px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 14px;
    }
    .hh-typing {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 8px 12px;
      background: #fff;
      border-radius: 12px;
      width: fit-content;
      border: 1px solid #e4e4e7;
    }
    .hh-dot {
      width: 6px;
      height: 6px;
      background: #047857;
      border-radius: 50%;
      animation: hh-bounce 1.4s infinite ease-in-out both;
    }
    .hh-dot:nth-child(1) { animation-delay: -0.32s; }
    .hh-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes hh-bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  `;
  document.head.appendChild(style);

  // Widget Container
  const container = document.createElement('div');
  container.id = 'hh-widget-container';
  container.innerHTML = `
    <button id="hh-widget-toggle" aria-label="Open Herbal Harbour AI Chat">🌿</button>
    <div id="hh-widget-window">
      <div class="hh-header">
        <div>
          <div class="hh-header-title">🌿 Herbal Harbour</div>
          <div class="hh-header-status">Apothecary Guide Active</div>
        </div>
        <button class="hh-close-btn" id="hh-widget-close">&times;</button>
      </div>
      <div class="hh-messages" id="hh-messages">
        <div class="hh-msg bot">Greetings! 🌿 I am Herbal-Harbour-Chat, your botanical apothecary assistant. How can I help your wellness journey today?</div>
      </div>
      <div class="hh-suggestions">
        <button class="hh-chip" data-msg="What herbs do you recommend for sleep?">😴 Sleep & Calm</button>
        <button class="hh-chip" data-msg="Do you have something for energy and brain focus?">⚡ Energy & Focus</button>
        <button class="hh-chip" data-msg="What are your local delivery options and rates?">📦 Delivery & Orders</button>
      </div>
      <div class="hh-input-bar">
        <input type="text" id="hh-input" placeholder="Ask about teas, tinctures, or remedies..." />
        <button class="hh-send-btn" id="hh-send">➤</button>
      </div>
    </div>
  `;
  document.body.appendChild(container);

  const toggleBtn = document.getElementById('hh-widget-toggle');
  const closeBtn = document.getElementById('hh-widget-close');
  const chatWindow = document.getElementById('hh-widget-window');
  const messagesBox = document.getElementById('hh-messages');
  const inputEl = document.getElementById('hh-input');
  const sendBtn = document.getElementById('hh-send');

  function toggleChat() {
    chatWindow.classList.toggle('hh-open');
    if (chatWindow.classList.contains('hh-open')) {
      inputEl.focus();
    }
  }

  toggleBtn.addEventListener('click', toggleChat);
  closeBtn.addEventListener('click', toggleChat);

  async function sendMessage(text) {
    if (!text || !text.trim()) return;
    text = text.trim();

    // Append user message
    const userDiv = document.createElement('div');
    userDiv.className = 'hh-msg user';
    userDiv.textContent = text;
    messagesBox.appendChild(userDiv);
    inputEl.value = '';
    messagesBox.scrollTop = messagesBox.scrollHeight;

    // Typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'hh-typing';
    typingDiv.id = 'hh-typing-indicator';
    typingDiv.innerHTML = '<div class="hh-dot"></div><div class="hh-dot"></div><div class="hh-dot"></div>';
    messagesBox.appendChild(typingDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;

    try {
      const res = await fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: visitorId,
          message: text,
          channel: 'website'
        })
      });
      const data = await res.json();
      const typing = document.getElementById('hh-typing-indicator');
      if (typing) typing.remove();

      const botDiv = document.createElement('div');
      botDiv.className = 'hh-msg bot';
      botDiv.textContent = data.reply || "I'm having trouble connecting to the apothecary right now. Please try again soon!";
      messagesBox.appendChild(botDiv);
      messagesBox.scrollTop = messagesBox.scrollHeight;
    } catch (e) {
      const typing = document.getElementById('hh-typing-indicator');
      if (typing) typing.remove();

      const botDiv = document.createElement('div');
      botDiv.className = 'hh-msg bot';
      botDiv.textContent = "Thank you for reaching out! We are currently experiencing a slight network delay. Please try again or message us directly on WhatsApp.";
      messagesBox.appendChild(botDiv);
      messagesBox.scrollTop = messagesBox.scrollHeight;
    }
  }

  sendBtn.addEventListener('click', () => sendMessage(inputEl.value));
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage(inputEl.value);
  });

  document.querySelectorAll('.hh-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const msg = chip.getAttribute('data-msg');
      sendMessage(msg);
    });
  });
})();
