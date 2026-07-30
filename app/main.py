from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.routes.chat import router as chat_router
from app.routes.raise_ticket import router as raise_ticket_router
from app.routes.support_route import router as support_route
from app.routes.websocket_router import router as websocket_router
from app.routes.notification_router import router as notification_router
from app.routes.support_auth import router as auth_router
# -----------------------------
# Database
# -----------------------------
from app.database.chatbot_db import Base, chatbot_engine

# Import ALL models so SQLAlchemy registers them
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.agent import Agent
from app.models.ticket_log import TicketLog
from app.models.notification_model import Notification

# Create chatbot tables (only if they don't already exist)
Base.metadata.create_all(bind=chatbot_engine)

# -----------------------------
# Static Files
# -----------------------------
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

# -----------------------------
# Routes
# -----------------------------
app.include_router(
    chat_router,
    prefix="/api",
)

app.include_router(
    raise_ticket_router,
)

app.include_router(
    support_route
)

app.include_router(
    websocket_router
)
app.include_router(
    notification_router
)

app.include_router(
    auth_router
)

# -----------------------------
# Demo Page
# -----------------------------
DEMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Widget Demo</title>

    <style>
        body{
            font-family:Arial,Helvetica,sans-serif;
            margin:40px;
        }

        .top-bar{
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:40px;
        }

        #agentLoginBtn{
            padding:10px 18px;
            border:none;
            background:#f5c400;
            color:#000;
            border-radius:6px;
            cursor:pointer;
            font-weight:bold;
        }

        .modal{
            display:none;
            position:fixed;
            inset:0;
            background:rgba(0,0,0,.5);
            justify-content:center;
            align-items:center;
        }

        .modal.show{
            display:flex;
        }

        .card{
            background:white;
            width:360px;
            padding:25px;
            border-radius:10px;
        }

        .card h2{
            margin-top:0;
        }

        .card input{
            width:100%;
            padding:10px;
            margin:10px 0;
            box-sizing:border-box;
        }

        .actions{
            display:flex;
            gap:10px;
            margin-top:20px;
        }

        .actions button{
            flex:1;
            padding:10px;
            cursor:pointer;
        }

        .notification-container{
            position:fixed;
            top:20px;
            right:20px;
            z-index:99999;
        }

        .notification{
            width:320px;
            background:white;
            border-left:5px solid #28a745;
            margin-bottom:10px;
            padding:15px;
            border-radius:8px;
            box-shadow:0 10px 30px rgba(0,0,0,.2);
            animation:slideIn .3s;
        }

        .notification h4{
            margin:0;
            font-size:15px;
        }

        .notification p{
            margin:5px 0 0;
            font-size:13px;
        }

        @keyframes slideIn{
            from{
                transform:translateX(100%);
                opacity:0;
            }
            to{
                transform:translateX(0);
                opacity:1;
            }
        }

        #notificationBell{
            position:relative;
            font-size:28px;
            cursor:pointer;
            user-select:none;
        }

        #notificationCount{
            position:absolute;
            top:-8px;
            right:-10px;
            background:red;
            color:white;
            min-width:18px;
            height:18px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:11px;
            font-weight:bold;
        }

        #notificationDropdown{
            display:none;
            position:absolute;
            top:40px;
            right:0;
            width:320px;
            max-height:360px;
            overflow-y:auto;
            background:white;
            border-radius:8px;
            box-shadow:0 10px 30px rgba(0,0,0,.2);
            z-index:9999;
        }

        #notificationDropdown.show{
            display:block;
        }

        #notificationDropdown .item{
            padding:12px 15px;
            border-bottom:1px solid #eee;
            font-size:13px;
        }

        #notificationDropdown .item h4{
            margin:0 0 4px;
            font-size:14px;
        }

        #notificationDropdown .empty{
            padding:20px;
            text-align:center;
            color:#888;
            font-size:13px;
        }

        /* --- join chat button (shared by toast + dropdown) --- */
        .join-btn{
            margin-top:8px;
            padding:6px 12px;
            border:none;
            border-radius:6px;
            background:#f5c400;
            font-size:12px;
            font-weight:bold;
            cursor:pointer;
        }
        .join-btn:disabled{
            opacity:.6;
            cursor:default;
        }

        /* --- agent live session panel --- */
        .session-panel{
            display:none;
            flex-direction:column;
            position:fixed;
            bottom:20px;
            left:20px;
            width:360px;
            height:520px;
            background:#fff;
            border-radius:12px;
            box-shadow:0 20px 45px rgba(0,0,0,.3);
            overflow:hidden;
            z-index:99998;
        }
        .session-panel.show{
            display:flex;
        }
        .session-header{
            background:#222;
            color:#fff;
            padding:12px 16px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            font-size:14px;
            font-weight:bold;
        }
        .session-header-actions{
            display:flex;
            align-items:center;
            gap:10px;
        }
        .session-header-actions button{
            border:none;
            background:none;
            color:#fff;
            font-size:18px;
            cursor:pointer;
        }
        .session-end-btn{
            background:#dc3545 !important;
            border-radius:6px;
            padding:6px 10px;
            font-size:12px !important;
            font-weight:bold;
        }
        .session-end-btn:disabled{
            opacity:.6;
            cursor:default;
        }
        .session-messages{
            flex:1;
            overflow-y:auto;
            padding:14px;
            background:#fafafa;
            display:flex;
            flex-direction:column;
            gap:8px;
        }
        .session-msg{
            max-width:80%;
            padding:8px 12px;
            border-radius:14px;
            font-size:13px;
            line-height:1.4;
            word-wrap:break-word;
        }
        .session-msg.user{
            background:#ececec;
            align-self:flex-start;
            border-radius:14px 14px 14px 4px;
        }
        .session-msg.ai{
            background:#e3f0ff;
            align-self:flex-start;
            border-radius:14px 14px 14px 4px;
        }
        .session-msg.agent{
            background:#ffe8a1;
            align-self:flex-end;
            border-radius:14px 14px 4px 14px;
        }
        .session-msg.system{
            align-self:center;
            background:none;
            color:#999;
            font-size:12px;
            font-style:italic;
        }
        .session-input{
            display:flex;
            border-top:1px solid #e6e6e6;
        }
        .session-input input{
            flex:1;
            border:none;
            outline:none;
            padding:12px;
            font-size:13px;
        }
        .session-input button{
            padding:0 16px;
            border:none;
            background:#f5c400;
            cursor:pointer;
            font-weight:bold;
        }
    </style>

</head>

<body>
<div id="notifications" class="notification-container"></div>

<div class="top-bar">

    <div>
        <h1>Demo Client Site</h1>
        <p>
            The chat widget below is embedded with a single script tag.
        </p>
    </div>

    <div style="display:flex;align-items:center;gap:15px;position:relative;">

        <div id="notificationBell">
            🔔
            <span id="notificationCount">0</span>

            <div id="notificationDropdown">
                <div class="empty">No notifications yet</div>
            </div>
        </div>

        <button id="agentLoginBtn">
            Agent Login
        </button>

    </div>

</div>

<div id="loginModal" class="modal">

    <div class="card">

        <h2>Support Agent Login</h2>

        <input id="email" type="email" placeholder="Email">
        <input id="password" type="password" placeholder="Password">

        <div class="actions">
            <button id="cancelBtn">Cancel</button>
            <button id="loginBtn">Login</button>
        </div>

    </div>

</div>

<!-- Agent-side live session panel: opens when an agent joins a chat -->
<div id="sessionPanel" class="session-panel">
    <div class="session-header">
        <span id="sessionTitle">Session</span>
        <div class="session-header-actions">
            <button id="sessionEndBtn" class="session-end-btn">End Chat</button>
            <button id="sessionCloseBtn" aria-label="Minimize">✕</button>
        </div>
    </div>
    <div id="sessionMessages" class="session-messages"></div>
    <div class="session-input">
        <input id="sessionInput" type="text" placeholder="Message the visitor...">
        <button id="sessionSendBtn">Send</button>
    </div>
</div>

<script>

// Endpoints for the join / history / live-chat feature.
// Adjust these if your backend runs somewhere else.
const API_BASE = "http://127.0.0.1:8000";
const WS_BASE = "ws://localhost:8000";

const modal = document.getElementById("loginModal");
const agentLoginBtn = document.getElementById("agentLoginBtn");
const notificationBell = document.getElementById("notificationBell");
const notificationDropdown = document.getElementById("notificationDropdown");
const notificationCountEl = document.getElementById("notificationCount");
const notificationsContainer = document.getElementById("notifications");

const sessionPanel = document.getElementById("sessionPanel");
const sessionTitleEl = document.getElementById("sessionTitle");
const sessionMessagesEl = document.getElementById("sessionMessages");
const sessionInputEl = document.getElementById("sessionInput");
const sessionSendBtn = document.getElementById("sessionSendBtn");
const sessionCloseBtn = document.getElementById("sessionCloseBtn");
const sessionEndBtn = document.getElementById("sessionEndBtn");

let socket = null; // notification socket (existing feature)
let notifications = [];
let unreadCount = 0;

let activeSession = null; // { id, socket } for the session currently open in the panel

agentLoginBtn.onclick = () => {

    if (localStorage.getItem("support_agent")) {

        disconnectSocket();
        closeAgentSessionPanel();

        localStorage.removeItem("support_agent");
        localStorage.removeItem("support_access_token");

        agentLoginBtn.textContent = "Agent Login";
        agentLoginBtn.style.background = "#f5c400";

        return;
    }

    modal.classList.add("show");
};

document.getElementById("cancelBtn").onclick = () => {
    modal.classList.remove("show");
};

// --- Notification bell dropdown ---
notificationBell.addEventListener("click", (e) => {
    e.stopPropagation();
    notificationDropdown.classList.toggle("show");

    if (notificationDropdown.classList.contains("show")) {
        unreadCount = 0;
        notifications.forEach(n => n.read = true);
        renderNotificationBell();
    }
});

document.addEventListener("click", (e) => {
    if (!notificationBell.contains(e.target)) {
        notificationDropdown.classList.remove("show");
    }
});

function renderNotificationBell() {
    notificationCountEl.textContent = unreadCount;
    notificationCountEl.style.display = unreadCount > 0 ? "flex" : "none";

    if (notifications.length === 0) {
        notificationDropdown.innerHTML = `<div class="empty">No notifications yet</div>`;
        return;
    }

    notificationDropdown.innerHTML = notifications.map(n => `
        <div class="item">
            <h4>${n.title}</h4>
            <p>${n.message}</p>
            ${n.session_id ? `<button class="join-btn" data-session-id="${n.session_id}">Join chat</button>` : ""}
        </div>
    `).join("");
}

function showNotification(title, message, sessionId) {

    const div = document.createElement("div");

    div.className = "notification";
    div.innerHTML = `
        <h4>${title}</h4>
        <p>${message}</p>
        ${sessionId ? `<button class="join-btn" data-session-id="${sessionId}">Join chat</button>` : ""}
    `;

    notificationsContainer.appendChild(div);

    setTimeout(() => {
        div.remove();
    }, 8000);
}

// One delegated listener handles "Join chat" clicks from both the toast
// popups and the dropdown list, since both get re-rendered/replaced often.
notificationsContainer.addEventListener("click", (e) => {
    const btn = e.target.closest(".join-btn");
    if (btn) joinSession(btn.dataset.sessionId, btn);
});

notificationDropdown.addEventListener("click", (e) => {
    const btn = e.target.closest(".join-btn");
    if (btn) joinSession(btn.dataset.sessionId, btn);
});

function connectNotificationSocket(agentId) {

    socket = new WebSocket(
        `ws://${window.location.host}/ws/support?agent_id=${agentId}`
    );

    socket.onopen = () => {
        console.log("Notification Connected");
    };

    socket.onmessage = (event) => {

        const data = JSON.parse(event.data);

        showNotification(data.title, data.message, data.session_id);

        notifications.unshift({
            ...data,
            read: false,
            created_at: new Date()
        });

        unreadCount++;
        renderNotificationBell();

        if (Notification.permission === "granted") {
            new Notification(data.title, {
                body: data.message,
                icon: "/favicon.ico"
            });
        }
    };

    socket.onclose = () => {
        console.log("Notification Disconnected");
    };
}

function disconnectSocket() {
    if (socket) {
        socket.close();
        socket = null;
    }
}

// ---------------------------------------------------------------
// Join chat feature
// ---------------------------------------------------------------

async function joinSession(sessionId, triggerBtn) {

    const agentData = JSON.parse(localStorage.getItem("support_agent") || "null");

    if (!agentData) {
        alert("You must be logged in as a support agent to join a chat.");
        return;
    }

    if (triggerBtn) {
        triggerBtn.disabled = true;
        triggerBtn.textContent = "Joining...";
    }

    try {

        const res = await fetch(`${API_BASE}/support/session/${sessionId}/join`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ agent_id: agentData.id })
        });

        if (!res.ok) {
            throw new Error("Join request failed");
        }

        notificationDropdown.classList.remove("show");
        await openAgentSessionPanel(sessionId, agentData.id);

    } catch (err) {
        alert("Unable to join this chat session.");
    } finally {
        if (triggerBtn) {
            triggerBtn.disabled = false;
            triggerBtn.textContent = "Join chat";
        }
    }
}

async function openAgentSessionPanel(sessionId, agentId) {

    closeAgentSessionPanel();

    activeSession = { id: sessionId, socket: null };

    sessionPanel.classList.add("show");
    sessionMessagesEl.innerHTML = "";
    sessionTitleEl.textContent = `Session ${sessionId.slice(0, 8)}`;

    await loadSessionHistory(sessionId);
    connectAgentChatSocket(sessionId, agentId);
}

async function loadSessionHistory(sessionId) {

    try {

        const res = await fetch(
            `${API_BASE}/support/session/${sessionId}`
        );

        const data = await res.json();

        const conversation = Array.isArray(data.conversation)
            ? data.conversation
            : [];

        conversation.forEach(msg => {

            appendSessionMessage(
                msg.sender_type,
                msg.message
            );

        });

    }
    catch (err) {

        appendSessionMessage(
            "system",
            "Couldn't load chat history."
        );

    }

}

function connectAgentChatSocket(sessionId, agentId) {

    const ws = new WebSocket(
        `${WS_BASE}/ws/chat/${sessionId}?participant=agent&agent_id=${agentId}`
    );

    ws.onopen = () => {
        appendSessionMessage("system", "You joined the chat.");
    };

    ws.onmessage = (event) => {

        const data = JSON.parse(event.data);

        if (data.type === "system") {
            appendSessionMessage("system", data.event === "user_left"
                ? "The visitor left the chat."
                : (data.event || "System update"));
            return;
        }

        // Don't re-render our own outgoing message if the backend echoes it.
        if (data.sender === "agent") return;

        appendSessionMessage(data.sender || "user", data.text);
    };

    ws.onclose = () => {
        appendSessionMessage("system", "Live connection closed.");
    };

    activeSession.socket = ws;
}

function appendSessionMessage(sender, text) {
    const el = document.createElement("div");
    el.className = `session-msg ${sender}`;
    el.textContent = text;
    sessionMessagesEl.appendChild(el);
    sessionMessagesEl.scrollTop = sessionMessagesEl.scrollHeight;
}

function sendAgentMessage() {

    const text = sessionInputEl.value.trim();
    if (!text || !activeSession || !activeSession.socket || activeSession.socket.readyState !== WebSocket.OPEN) {
        return;
    }

    activeSession.socket.send(JSON.stringify({ type: "message", text }));
    appendSessionMessage("agent", text);
    sessionInputEl.value = "";
}

// Minimize: just hides the panel and drops the agent's own socket.
// The session itself is untouched - the agent (or another agent) can
// join it again later, it is NOT marked resolved/closed on the backend.
function closeAgentSessionPanel() {
    if (activeSession && activeSession.socket) {
        activeSession.socket.close();
    }
    activeSession = null;
    sessionPanel.classList.remove("show");
}

// End Chat: actually resolves/closes the session on the backend.
async function endSupportSession() {

    if (!activeSession) return;

    const agentData = JSON.parse(localStorage.getItem("support_agent") || "null");
    if (!agentData) return;

    const note = window.prompt(
        "Resolution note for this session:",
        "Resolved all queries."
    );

    if (note === null) return; // agent cancelled the prompt, don't close anything

    sessionEndBtn.disabled = true;
    sessionEndBtn.textContent = "Ending...";

    try {

        const res = await fetch(
            `${API_BASE}/support/session/${activeSession.id}/close`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agent_id: agentData.id,
                    resolution_note: note || "Resolved all queries."
                })
            }
        );

        if (!res.ok) {
            throw new Error("Close request failed");
        }

        appendSessionMessage("system", "Chat session closed.");

    } catch (err) {
        alert("Unable to close this chat session.");
        sessionEndBtn.disabled = false;
        sessionEndBtn.textContent = "End Chat";
        return;
    }

    sessionEndBtn.disabled = false;
    sessionEndBtn.textContent = "End Chat";

    closeAgentSessionPanel();
}

sessionSendBtn.onclick = sendAgentMessage;
sessionInputEl.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendAgentMessage();
});
sessionCloseBtn.onclick = closeAgentSessionPanel;
sessionEndBtn.onclick = endSupportSession;

// ---------------------------------------------------------------

if (Notification.permission === "default") {
    Notification.requestPermission();
}

const storedAgent = localStorage.getItem("support_agent");

if (storedAgent) {

    const agent = JSON.parse(storedAgent);

    agentLoginBtn.textContent = "Logout";
    agentLoginBtn.style.background = "#dc3545";

    connectNotificationSocket(agent.id);
}

document.getElementById("loginBtn").onclick = async () => {

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {

        const response = await fetch("/api/support/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Login Failed");
            return;
        }

        localStorage.setItem("support_access_token", data.access_token);
        localStorage.setItem("support_agent", JSON.stringify(data.agent));

        modal.classList.remove("show");

        alert("Logged in as " + data.agent.name);
        agentLoginBtn.textContent = "Logout";
        agentLoginBtn.style.background = "#dc3545";

        connectNotificationSocket(data.agent.id);

    } catch (err) {
        alert("Unable to login.");
    }
};

renderNotificationBell();

</script>

<script
    src="/chatbot-widget.js"
    data-chatbot-id="site-a"
    data-theme-color="#f5c400"
    data-position="bottom-right">
</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return DEMO_HTML


@app.get("/chatbot-widget.js")
async def widget_script():
    widget_path = STATIC_DIR / "chatbot-widget.js"

    if not widget_path.exists():
        return HTMLResponse(
            content=f"chatbot-widget.js not found at {widget_path}",
            status_code=500,
        )

    return FileResponse(
        str(widget_path),
        media_type="application/javascript",
    )


@app.get("/health")
async def health():
    return {
        "message": "Chatbot running successfully"
    }