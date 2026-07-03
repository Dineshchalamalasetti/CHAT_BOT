from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user, is_premium_active, user_has_chat_access
from app.chat_service import ChatServiceError, generate_reply, get_assistant_info
from app.config import CORS_ORIGINS
from app.database import get_db, init_db
from app.models import ChatMessage, User
from app.routers import auth_router, payment_router

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="AI Chat Assistant",
    description="Intelligent chatbot with auth and payments.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(payment_router.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatMessagePayload(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    messages: list[ChatMessagePayload] = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    role: str = "assistant"


@app.on_event("startup")
def on_startup() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/info")
async def info() -> dict:
    return get_assistant_info()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must be from the user.")

    if not user_has_chat_access(user):
        raise HTTPException(
            status_code=402,
            detail="Free message limit reached. Subscribe to continue chatting.",
        )

    payload = [message.model_dump() for message in request.messages]

    try:
        reply = generate_reply(payload)
    except ChatServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    last_user_message = request.messages[-1].content
    db.add(ChatMessage(user_id=user.id, role="user", content=last_user_message))
    db.add(ChatMessage(user_id=user.id, role="assistant", content=reply))

    if not is_premium_active(user):
        user.free_messages_used += 1

    db.commit()

    return ChatResponse(reply=reply)
