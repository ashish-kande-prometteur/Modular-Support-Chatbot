/*
 * Embeddable AI Support Chat Widget
 *
 * Usage (single script tag on the host site):
 *   <script
 *     src="https://your-domain.com/chatbot-widget.js"
 *     data-chatbot-id="site-a"
 *     data-theme-color="#f5c400"
 *     data-position="bottom-right"
 *     data-api-base="https://your-domain.com">
 *   </script>
 *
 * data-chatbot-id : identifies which client/site this widget belongs to
 * data-theme-color: accent color for the button/header (optional)
 * data-position   : "bottom-right" (default) or "bottom-left"
 * data-api-base   : origin of the backend, defaults to this script's own origin
 *
 * Everything the widget knows about the backend is exactly two REST calls:
 *   POST {apiBase}/api/chat
 *   POST {apiBase}/api/feedback
 * It has no other knowledge of what powers the backend.
 */

(function () {
  "use strict";

  const CURRENT_SCRIPT = document.currentScript;

  const config = {
    chatbotId: CURRENT_SCRIPT.dataset.chatbotId || "default",
    themeColor: CURRENT_SCRIPT.dataset.themeColor || "#f5c400",
    position: CURRENT_SCRIPT.dataset.position || "bottom-right",
    apiBase:
      CURRENT_SCRIPT.dataset.apiBase ||
      new URL(CURRENT_SCRIPT.src, window.location.href).origin
  };

  let sessionId = null;
  let externalUserId = localStorage.getItem("chatbot_external_user_id");

  if (!externalUserId) {
    externalUserId = crypto.randomUUID();
    localStorage.setItem(
      "chatbot_external_user_id",
      externalUserId
    );
  }
  const isLeft = config.position === "bottom-left";

  // ------------------------------------------------------------
  // Shadow DOM host - isolates widget styles from the host page,
  // and isolates the host page's styles from the widget.
  // ------------------------------------------------------------
  const host = document.createElement("div");
  host.id = "ai-support-chat-widget-host";
  const shadow = host.attachShadow({ mode: "open" });

  const style = document.createElement("style");
  style.textContent = `
    :host { all: initial; }
    *, *::before, *::after {
      box-sizing: border-box;
      font-family: Arial, Helvetica, sans-serif;
    }

    .chat-btn {
      position: fixed;
      ${isLeft ? "left: 25px;" : "right: 25px;"}
      bottom: 25px;
      width: 62px;
      height: 62px;
      border: none;
      border-radius: 50%;
      background: ${config.themeColor};
      font-size: 26px;
      cursor: pointer;
      box-shadow: 0 10px 25px rgba(0, 0, 0, .25);
      z-index: 2147483000;
      transition: transform .2s ease;
    }
    .chat-btn:hover { transform: scale(1.08); }

    .chat-window {
      position: fixed;
      ${isLeft ? "left: 25px;" : "right: 25px;"}
      bottom: 100px;
      width: 380px;
      height: 600px;
      max-width: calc(100vw - 20px);
      max-height: 75vh;
      background: #fff;
      border-radius: 18px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      visibility: hidden;
      opacity: 0;
      pointer-events: none;
      transform: translateY(24px);
      transition: opacity .2s ease, transform .2s ease, visibility .2s;
      box-shadow: 0 20px 45px rgba(0, 0, 0, .3);
      z-index: 2147483000;
    }
    .chat-window.show {
      visibility: visible;
      opacity: 1;
      pointer-events: auto;
      transform: translateY(0);
    }

    .chat-header {
      background: ${config.themeColor};
      color: #fff;
      padding: 16px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 15px;
      font-weight: bold;
    }
    .chat-header button {
      border: none;
      background: none;
      color: #fff;
      font-size: 20px;
      line-height: 1;
      cursor: pointer;
    }

    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #fafafa;
    }

    .msg {
      max-width: 82%;
      margin-bottom: 10px;
      padding: 10px 14px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.4;
      word-wrap: break-word;
    }
    .msg.user {
      background: #ffe8a1;
      margin-left: auto;
      border-radius: 16px 16px 4px 16px;
    }
    .msg.bot {
      background: #ececec;
      border-radius: 16px 16px 16px 4px;
    }

    .feedback-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: -2px 0 14px 2px;
      font-size: 12px;
      color: #888;
    }
    .feedback-row button {
      border: 1px solid #ddd;
      background: #fff;
      border-radius: 8px;
      padding: 3px 9px;
      cursor: pointer;
      font-size: 13px;
    }
    .feedback-row button:hover { background: #f2f2f2; }

    .chat-input {
      display: flex;
      border-top: 1px solid #e6e6e6;
      background: #fff;
    }
    .chat-input input {
      flex: 1;
      border: none;
      outline: none;
      padding: 15px;
      font-size: 14px;
    }
    .chat-input button {
      width: 58px;
      border: none;
      background: ${config.themeColor};
      color: #fff;
      cursor: pointer;
      font-size: 18px;
    }

    @media (max-width: 480px) {
      .chat-window {
        left: 10px;
        right: 10px;
        width: auto;
        bottom: 85px;
        height: 70vh;
      }
    }
  `;

  const markup = document.createElement("div");
  markup.innerHTML = `
    <button class="chat-btn" aria-label="Open chat">💬</button>
    <div class="chat-window">
      <div class="chat-header">
        <span>Chat with us</span>
        <button class="close-btn" aria-label="Close chat">✕</button>
      </div>
      <div class="messages"></div>
      <div class="chat-input">
        <input type="text" placeholder="Type your message..." />
        <button class="send-btn" aria-label="Send">➤</button>
      </div>
    </div>
  `;

  shadow.appendChild(style);
  shadow.appendChild(markup);
  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(host);
  });
  if (document.readyState !== "loading") {
    document.body.appendChild(host);
  }

  const toggleBtn = shadow.querySelector(".chat-btn");
  const closeBtn = shadow.querySelector(".close-btn");
  const chatWindow = shadow.querySelector(".chat-window");
  const messagesEl = shadow.querySelector(".messages");
  const input = shadow.querySelector("input");
  const sendBtn = shadow.querySelector(".send-btn");

  toggleBtn.addEventListener("click", () => {
    chatWindow.classList.add("show");
  });

  closeBtn.addEventListener("click", () => {
    chatWindow.classList.remove("show");
  });

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  function appendMessage(text, sender) {
    const el = document.createElement("div");
    el.className = `msg ${sender}`;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendFeedbackPrompt(forSessionId) {
    const row = document.createElement("div");
    row.className = "feedback-row";
    row.innerHTML = `<span>Was this helpful?</span>`;

    const up = document.createElement("button");
    up.type = "button";
    up.textContent = "👍";

    const down = document.createElement("button");
    down.type = "button";
    down.textContent = "👎";

    up.addEventListener("click", () => sendFeedback(forSessionId, "up", row));
    down.addEventListener("click", () => sendFeedback(forSessionId, "down", row));

    row.appendChild(up);
    row.appendChild(down);
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendFeedback(forSessionId, rating, rowEl) {
    rowEl.innerHTML = `<span>Thanks for the feedback!</span>`;

    try {
      await fetch(`${config.apiBase}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chatbot_id: config.chatbotId,
          session_id: forSessionId,
          rating: rating
        })
      });
    } catch (err) {
      // Feedback is best-effort - don't disrupt the chat on failure.
    }
  }

  async function sendMessage() {
    const question = input.value.trim();
    if (!question) return;

    appendMessage(question, "user");
    input.value = "";

    try {
      const res = await fetch(`${config.apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chatbot_id: config.chatbotId,
          session_id: sessionId,
          external_user_id: externalUserId,
          widget_source: "website",
          question: question
        })
      });

      const data = await res.json();

      sessionId = data.session_id || sessionId;

      // Backend may return a flat string ("answer": "...") or the
      // older nested shape ("answer": {answer, confidence, ...}).
      // Handle both so the widget never renders "[object Object]".
      const answerText =
        typeof data.answer === "string"
          ? data.answer
          : data.answer && typeof data.answer.answer === "string"
            ? data.answer.answer
            : "Sorry, I couldn't understand the response.";

      appendMessage(answerText, "bot");

      if (data.show_feedback) {
        appendFeedbackPrompt(sessionId);
      }
    } catch (err) {
      appendMessage(
        "Sorry, I couldn't connect to the server. Please try again.",
        "bot"
      );
    }
  }
})();