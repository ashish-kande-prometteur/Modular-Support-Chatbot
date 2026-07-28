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
</head>
<body>
    <div style="padding:50px;font-family:Arial,Helvetica,sans-serif;">
        <h1>Demo Client Site</h1>
        <p>
            The chat widget below is embedded with a single script tag.
            It renders inside a Shadow DOM, so it does not affect and is
            not affected by this page's own styles.
        </p>
    </div>

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