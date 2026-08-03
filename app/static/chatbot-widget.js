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

function generateUUID() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
    }

    // Fallback for browsers/environments without crypto.randomUUID()
    return (
        "user_" +
        Date.now() +
        "_" +
        Math.random().toString(36).substring(2, 10)
    );
}

// let externalUserId = localStorage.getItem("chatbot_external_user_id");

if (!externalUserId) {
    externalUserId =
        window.crypto && typeof window.crypto.randomUUID === "function"
            ? window.crypto.randomUUID()
            : "user_" +
              Date.now() +
              "_" +
              Math.random().toString(36).substring(2, 10);

    localStorage.setItem(
        "chatbot_external_user_id",
        externalUserId
    );
}
  const isLeft = config.position === "bottom-left";

  // Live-chat state. agentActive flips true once the backend tells us
  // an agent joined this session over the WebSocket below.
  let liveSocket = null;
  let agentActive = false;
  let widgetDisabled = false;

  function syncWidgetVisibility() {
    const agentLoggedIn = !!localStorage.getItem("support_agent");
    widgetDisabled = agentLoggedIn;

    host.style.display = agentLoggedIn ? "none" : "";
    chatWindow.classList.remove("show");
    toggleBtn.disabled = agentLoggedIn;
    sendBtn.disabled = agentLoggedIn;
    input.disabled = agentLoggedIn;
    toggleBtn.setAttribute("aria-disabled", agentLoggedIn ? "true" : "false");
  }


  // ------------------------------------------------------------
  // Session resolution / inactivity state
  // ------------------------------------------------------------

  let resolutionTimer = null;
  let presenceTimer = null;
  let abandonTimer = null;

  let activeSessionPrompt = null;

  const RESOLUTION_WAIT_MS = 60000;
  // const RESOLUTION_WAIT_MS = 60000;
  const PRESENCE_WAIT_MS = 60000;
  const ABANDON_WAIT_MS = 60000;

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
    .chat-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }

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
    .msg.agent {
      background: #d8ecff;
      border-radius: 16px 16px 16px 4px;
    }
    .msg.system {
      background: none;
      color: #999;
      font-size: 12px;
      font-style: italic;
      text-align: center;
      max-width: 100%;
      margin: 4px 0 14px;
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

    .session-prompt {
      margin: 8px 0 14px 0;
      padding: 12px;
      background: #fff;
      border: 1px solid #e6e6e6;
      border-radius: 12px;
      font-size: 13px;
    }

    .session-prompt-text {
      margin-bottom: 10px;
      color: #333;
    }

    .session-prompt-actions {
      display: flex;
      gap: 8px;
    }

    .session-prompt button {
      border: 1px solid #ddd;
      background: #fff;
      border-radius: 8px;
      padding: 6px 14px;
      cursor: pointer;
    }

    .session-prompt button:hover {
      background: #f2f2f2;
    }

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
  .sender-name {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 4px;
    color: #2b6cb0;
}

    .feedback-popup {
      text-align: center;
      padding: 16px 12px;
      margin: 8px 0 14px;
      background: #f9f9f9;
      border-radius: 12px;
      border: 1px solid #e6e6e6;
    }
    .feedback-popup .feedback-title {
      font-size: 14px;
      font-weight: 600;
      color: #333;
      margin-bottom: 12px;
    }
    .feedback-popup button {
      border: 1px solid #ddd;
      background: #fff;
      border-radius: 10px;
      padding: 8px 20px;
      margin: 0 6px;
      cursor: pointer;
      font-size: 14px;
      transition: background .15s ease, transform .1s ease;
    }
    .feedback-popup button:hover {
      background: #f0f0f0;
      transform: scale(1.05);
    }

  .msg.thinking {
    background: #ececec;
    color: #666;
    font-style: italic;
}

.dots::after {
    content: "";
    animation: dots 1.2s infinite;
}

@keyframes dots {
    0% {
        content: "";
    }
    33% {
        content: ".";
    }
    66% {
        content: "..";
    }
    100% {
        content: "...";
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
  let thinkingMessage = null;


  async function streamMessage(text, sender) {

      const el = document.createElement("div");
      el.className = `msg ${sender}`;

      messagesEl.appendChild(el);

      let current = "";

      for (const ch of text) {

          current += ch;

          el.textContent = "🤖 " + current;

          messagesEl.scrollTop = messagesEl.scrollHeight;

          await new Promise(r => setTimeout(r, 12));
      }
  }

  function showThinking() {
    thinkingMessage = document.createElement("div");
    thinkingMessage.className = "msg bot thinking";
    thinkingMessage.innerHTML = `
        🤖 <span class="thinking-text">
            Thinking<span class="dots"></span>
        </span>
    `;

    messagesEl.appendChild(thinkingMessage);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideThinking() {
      if (thinkingMessage) {
          thinkingMessage.remove();
          thinkingMessage = null;
      }
  }

  window.addEventListener("support-agent-auth-changed", syncWidgetVisibility);
  window.addEventListener("storage", (event) => {
    if (event.key === "support_agent") {
      syncWidgetVisibility();
    }
  });

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

  function getMessagePrefix(sender) {
    if (sender === "user") return "🧑‍💼";
    if (sender === "agent") return "🧑‍💼";
    if (sender === "bot") return "🤖";
    return "ℹ️";
  }

  function appendMessage(text, sender, senderName = null) {
      const el = document.createElement("div");
      el.className = `msg ${sender}`;
      const prefix = getMessagePrefix(sender);

      if (sender === "agent" && senderName) {
          el.innerHTML = `
              <div class="sender-name">${prefix} ${senderName}</div>
              <div>${text}</div>
          `;
      } else {
          el.textContent = `${prefix} ${text}`;
      }

      messagesEl.appendChild(el);
      messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function clearSessionTimers() {
    if (resolutionTimer) {
      clearTimeout(resolutionTimer);
      resolutionTimer = null;
    }

    if (presenceTimer) {
      clearTimeout(presenceTimer);
      presenceTimer = null;
    }

    if (abandonTimer) {
      clearTimeout(abandonTimer);
      abandonTimer = null;
    }
  }

  function removeSessionPrompt() {
  if (activeSessionPrompt) {
    activeSessionPrompt.remove();
    activeSessionPrompt = null;
  }
  }

  function resetSessionFlow() {
    clearSessionTimers();
    removeSessionPrompt();
  }


  function startResolutionTimer() {
    resetSessionFlow();

    if (!sessionId) {
      return;
    }

    resolutionTimer = setTimeout(() => {
      showResolutionPrompt();
    }, RESOLUTION_WAIT_MS);
  }

  function showResolutionPrompt() {
    resetSessionFlow();

    const prompt = document.createElement("div");
    prompt.className = "session-prompt";

    prompt.innerHTML = `
      <div class="session-prompt-text">
        Did this resolve your issue?
      </div>

      <div class="session-prompt-actions">
        <button type="button" class="resolution-yes">
          Yes
        </button>

        <button type="button" class="resolution-no">
          No
        </button>
      </div>
    `;

    activeSessionPrompt = prompt;

    messagesEl.appendChild(prompt);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    const yesButton = prompt.querySelector(".resolution-yes");
    const noButton = prompt.querySelector(".resolution-no");

    yesButton.addEventListener("click", () => {
      confirmResolution();
    });

    noButton.addEventListener("click", () => {
      handleResolutionNo();
    });

    presenceTimer = setTimeout(() => {
      showPresencePrompt();
    }, PRESENCE_WAIT_MS);
  }


  async function confirmResolution() {
  resetSessionFlow();

  if (!sessionId) {
    return;
  }

  try {
    const response = await fetch(
      `${config.apiBase}/support/session/${sessionId}/confirm-resolution`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          external_user_id: externalUserId
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Unable to confirm resolution."
      );
    }

    appendMessage(
      "Thanks. Your resolution has been recorded.",
      "system"
    );

  } catch (err) {
    console.error(
      "Failed to confirm resolution:",
      err
    );
  }
}


  function handleResolutionNo() {
    resetSessionFlow();

    appendMessage(
      "No problem. Please continue and tell us what you still need help with.",
      "system"
    );

    input.focus();
  }


  function showPresencePrompt() {
    resetSessionFlow();

    const prompt = document.createElement("div");
    prompt.className = "session-prompt";

    prompt.innerHTML = `
      <div class="session-prompt-text">
        Are you still there?
      </div>

      <div class="session-prompt-actions">
        <button type="button" class="presence-yes">
          Yes
        </button>
      </div>
    `;

    activeSessionPrompt = prompt;

    messagesEl.appendChild(prompt);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    const yesButton = prompt.querySelector(".presence-yes");

    yesButton.addEventListener("click", () => {
      handleStillHere();
    });

    abandonTimer = setTimeout(() => {
      abandonSession();
    }, ABANDON_WAIT_MS);
  }


  function handleStillHere() {
  resetSessionFlow();

  appendMessage(
    "Thanks. The conversation will remain active.",
    "system"
  );

  startResolutionTimer();
}

  async function abandonSession() {
    resetSessionFlow();

    if (!sessionId) {
      return;
    }

    try {
      const response = await fetch(
        `${config.apiBase}/support/session/${sessionId}/abandon`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            external_user_id: externalUserId
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to mark session as abandoned."
        );
      }

      appendMessage(
        "This conversation was closed due to inactivity.",
        "system"
      );

    } catch (err) {
      console.error(
        "Failed to mark session as abandoned:",
        err
      );
    }
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

  // ------------------------------------------------------------
  // Live agent chat (new)
  // ------------------------------------------------------------
async function submitFeedback(helpful) {

    await fetch(
        `${config.apiBase}/api/chat/session/${sessionId}/feedback`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                helpful: helpful,
            }),
        }
    );

    appendMessage(
        "Thank you for your feedback.",
        "system",
    );

    chatWindow.classList.remove("show");
}

  function showFeedbackPopup() {

      const popup = document.createElement("div");

      popup.className = "feedback-popup";

      const title = document.createElement("div");
      title.className = "feedback-title";
      title.textContent = "Was this conversation helpful?";

      const yesBtn = document.createElement("button");
      yesBtn.textContent = "👍 Yes";

      const noBtn = document.createElement("button");
      noBtn.textContent = "👎 No";

      yesBtn.addEventListener("click", () => submitFeedback(true));
      noBtn.addEventListener("click", () => submitFeedback(false));

      popup.appendChild(title);
      popup.appendChild(yesBtn);
      popup.appendChild(noBtn);

      messagesEl.appendChild(popup);
      messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function connectLiveSocket(sid) {

    if (liveSocket) {
      liveSocket.close();
    }

    // Derive ws(s):// from the configured http(s) apiBase.
    const wsBase = config.apiBase.replace(/^http/, "ws");
    liveSocket = new WebSocket(
      `${wsBase}/ws/chat/${sid}?participant=user&external_user_id=${externalUserId}`
    );

    liveSocket.onmessage = (event) => {

      let data;
      try {
        data = JSON.parse(event.data);
      } catch (err) {
        return;
      }

    if (data.type === "system") {

        if (data.event === "agent_joined") {

            agentActive = true;

            appendMessage(
                data.agent_name + " joined the chat",
                "system"
            );

            return;

          agentActive = true;
          appendMessage(
            data.agent_name
              ? `${data.agent_name} joined the chat`
              : "An agent joined the chat",
            "system"
          );
        } else if (data.event === "agent_left") {
          agentActive = false;

          appendMessage(
            "The agent left. You're back to chatting with our AI.",
            "system"
          );

        }

        if (data.event === "feedback_required") {

            agentActive = false;

            showFeedbackPopup();

            return;
        }

        if (data.event === "agent_left") {

            agentActive = false;

            appendMessage(
                "Support session ended.",
                "system"
            );

            return;
        }
    }

      // Don't display the user's own WebSocket message again.
      if (data.sender === "user") {
        return;
      }

      if (data.sender === "agent") {

        appendMessage(
          data.text,
          "agent",
          data.agent_name
        );

        // Start resolution flow after agent response.
        startResolutionTimer();

      } else {

        appendMessage(
          data.text,
          "bot"
        );

        // Start resolution flow after bot response.
        startResolutionTimer();
      }
    };

    liveSocket.onclose = () => {
      agentActive = false;
    };
  }

  // ------------------------------------------------------------

  syncWidgetVisibility();

  async function sendMessage() {
    if (widgetDisabled) return;

    const question = input.value.trim();
    if (!question) return;
    resetSessionFlow();

    appendMessage(question, "user");
    input.value = "";

    if (agentActive && liveSocket && liveSocket.readyState === WebSocket.OPEN) {
    liveSocket.send(
        JSON.stringify({
            type: "message",
            text: question,
        })
    );
    return;
  }

  showThinking();

    // While an agent is live on this session, skip the AI REST call
    // entirely and send straight over the WebSocket.
    if (agentActive && liveSocket && liveSocket.readyState === WebSocket.OPEN) {
      liveSocket.send(JSON.stringify({ type: "message", text: question }));
      return;
    }

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
      hideThinking();
      const previousSessionId = sessionId;
      sessionId = data.session_id || sessionId;

      // First time we learn our session_id, open the background socket
      // that listens for an agent joining.
      if (sessionId && sessionId !== previousSessionId) {
        connectLiveSocket(sessionId);
      }

      // Backend may return a flat string ("answer": "...") or the
      // older nested shape ("answer": {answer, confidence, ...}).
      // Handle both so the widget never renders "[object Object]".
      let answerText = "";

      if (typeof data.answer === "string") {

          answerText = data.answer;

      } else if (
          data.answer &&
          typeof data.answer.answer === "string"
      ) {

          answerText = data.answer.answer;

      }

      if (answerText) {
          streamMessage(answerText, "bot");
          startResolutionTimer();
      }

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
