import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Provider: groq | gemini | openai
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower().strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatbot.db")
JWT_SECRET = os.getenv("JWT_SECRET", "K8xP2mN9vQ4zR7tY1aBcDeFgHiJkLmNoPqRsTuVwXyZ")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
FREE_MESSAGE_LIMIT = int(os.getenv("FREE_MESSAGE_LIMIT", "20"))

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_Szzj7ZVdQoqeGa")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "FfDzCUPXjH05Zh0vmlLatMeW")
PREMIUM_PLAN_AMOUNT_PAISE = int(os.getenv("PREMIUM_PLAN_AMOUNT_PAISE", "9900"))
PREMIUM_PLAN_DAYS = int(os.getenv("PREMIUM_PLAN_DAYS", "30"))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    if origin.strip()
]
