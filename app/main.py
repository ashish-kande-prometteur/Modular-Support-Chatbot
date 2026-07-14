from fastapi import FastAPI

from app.routes.chat import router as chat_router
app = FastAPI()

app.include_router(
    chat_router,
    prefix="/api"
)


@app.get("/")
async def health():
    return {
        "message":
            "Chatbot running successfully"
    }