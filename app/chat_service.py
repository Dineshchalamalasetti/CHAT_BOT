from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    MAX_HISTORY_MESSAGES,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from app.prompts import SYSTEM_PROMPT


class ChatServiceError(Exception):
    """Raised when the chat service cannot complete a request."""


PROVIDER_LABELS = {
    "openai": "OpenAI",
    "groq": "Groq (free tier)",
    "gemini": "Google Gemini (free tier)",
}


def _trim_history(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    if len(messages) <= MAX_HISTORY_MESSAGES:
        return messages
    return messages[-MAX_HISTORY_MESSAGES:]


def _build_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"role": "system", "content": SYSTEM_PROMPT}, *_trim_history(messages)]


def _get_client_and_model() -> tuple[OpenAI, str]:
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ChatServiceError(
                "OPENAI_API_KEY is not configured. Add it to .env or switch AI_PROVIDER to groq/gemini."
            )
        return OpenAI(api_key=OPENAI_API_KEY), OPENAI_MODEL

    if AI_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise ChatServiceError(
                "GROQ_API_KEY is not configured. Get a free key at https://console.groq.com/keys"
            )
        return (
            OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY),
            GROQ_MODEL,
        )

    if AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ChatServiceError(
                "GEMINI_API_KEY is not configured. Get a free key at https://aistudio.google.com/apikey"
            )
        return (
            OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=GEMINI_API_KEY,
            ),
            GEMINI_MODEL,
        )

    raise ChatServiceError(
        f"Unknown AI_PROVIDER '{AI_PROVIDER}'. Use: gemini, groq, or openai."
    )


def _is_configured() -> bool:
    if AI_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    if AI_PROVIDER == "groq":
        return bool(GROQ_API_KEY)
    if AI_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY)
    return False


def _current_model() -> str | None:
    if not _is_configured():
        return None
    return {
        "openai": OPENAI_MODEL,
        "groq": GROQ_MODEL,
        "gemini": GEMINI_MODEL,
    }.get(AI_PROVIDER)


def generate_reply(messages: list[dict[str, str]]) -> str:
    client, model = _get_client_and_model()
    payload = _build_messages(messages)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=payload,
            temperature=0.7,
        )
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        if AI_PROVIDER == "gemini" and "429" in message:
            message += (
                " Your Gemini free-tier quota is exhausted or not enabled. "
                "Switch to Groq in .env: set AI_PROVIDER=groq and add a free key from https://console.groq.com/keys"
            )
        raise ChatServiceError(f"Failed to generate a response: {message}") from exc

    content = response.choices[0].message.content
    if not content:
        raise ChatServiceError("The model returned an empty response.")

    return content.strip()


def get_assistant_info() -> dict[str, Any]:
    return {
        "name": "DEN AI Assistant",
        "provider": AI_PROVIDER,
        "provider_label": PROVIDER_LABELS.get(AI_PROVIDER, AI_PROVIDER),
        "model": _current_model(),
        "configured": _is_configured(),
        "max_history_messages": MAX_HISTORY_MESSAGES,
        "capabilities": [
            {
                "label": "Programming & Debugging",
                "prompt": "Help me debug a programming problem. I'll describe the issue — ask clarifying questions and suggest fixes step by step.",
            },
            {
                "label": "Data Science & Machine Learning",
                "prompt": "Explain a machine learning concept from beginner to intermediate level with a practical Python example.",
            },
            {
                "label": "SQL & Databases",
                "prompt": "Teach me an important SQL concept with example queries and explain how to optimize them.",
            },
            {
                "label": "Linux & Networking",
                "prompt": "Explain a useful Linux or networking concept with practical commands and real-world examples.",
            },
            {
                "label": "Interview Preparation",
                "prompt": "Help me prepare for a technical interview. Start with an easy question and increase difficulty based on my answers.",
            },
            {
                "label": "Technical Writing",
                "prompt": "Help me write clear technical documentation. Ask what topic I need and draft a professional outline.",
            },
            {
                "label": "Step-by-step Tutoring",
                "prompt": "Act as my tutor. Ask what I want to learn, then teach it step by step from basics to advanced.",
            },
        ],
        "alternatives": [
            {"id": "gemini", "label": "Gemini", "note": "Free tier from Google"},
            {"id": "groq", "label": "Groq", "note": "Free cloud API, fast responses"},
            {"id": "openai", "label": "OpenAI", "note": "Paid, requires billing"},
        ],
    }
