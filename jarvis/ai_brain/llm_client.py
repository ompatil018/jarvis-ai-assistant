"""
ai_brain/llm_client.py — LLM API Client
Supports: OpenAI (primary) → Groq (fallback) → Ollama (local fallback)
Includes retry logic, token management, and provider auto-switching.
"""

import logging
import time
from typing import List, Dict, Optional

from config import (
    LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    OPENAI_API_KEY, GROQ_API_KEY
)

logger = logging.getLogger("ai_brain.llm")

# ── Provider imports ───────────────────────────────────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(OPENAI_API_KEY)
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = bool(GROQ_API_KEY)
except ImportError:
    GROQ_AVAILABLE = False


class LLMClient:
    """Unified LLM client with automatic provider fallback."""

    def __init__(self) -> None:
        self._client   = None
        self._provider = LLM_PROVIDER
        self._model    = LLM_MODEL
        self._init_client()

    def _init_client(self) -> None:
        if self._provider == "openai" and OPENAI_AVAILABLE:
            self._client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info(f"LLM: OpenAI ({self._model})")

        elif self._provider == "groq" or (not OPENAI_AVAILABLE and GROQ_AVAILABLE):
            self._client   = Groq(api_key=GROQ_API_KEY)
            self._provider = "groq"
            self._model    = "llama3-70b-8192"
            logger.info(f"LLM: Groq ({self._model})")

        elif self._provider == "ollama":
            try:
                from openai import OpenAI as OllamaClient
                self._client   = OllamaClient(
                    base_url="http://localhost:11434/v1",
                    api_key="ollama"
                )
                self._provider = "ollama"
                self._model    = "llama3"
                logger.info("LLM: Ollama (local)")
            except Exception as exc:
                logger.error(f"Ollama init failed: {exc}")

        if self._client is None:
            logger.warning(
                "No LLM provider configured — responses will be rule-based only. "
                "Set OPENAI_API_KEY or GROQ_API_KEY in .env"
            )

    # ─── Public API ───────────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int    = LLM_MAX_TOKENS,
        retries: int       = 3,
    ) -> str:
        """Send a chat completion request, returning the response text."""
        if self._client is None:
            return self._rule_based_fallback(messages)

        last_error = None
        for attempt in range(1, retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = response.choices[0].message.content.strip()
                logger.debug(f"LLM response: {text[:120]}...")
                return text

            except Exception as exc:
                last_error = exc
                wait = 2 ** attempt
                logger.warning(f"LLM attempt {attempt}/{retries} failed: {exc} — retrying in {wait}s")
                time.sleep(wait)

        logger.error(f"All LLM retries exhausted: {last_error}")
        return "I'm having trouble connecting to my brain right now. Please check your API key."

    def is_available(self) -> bool:
        return self._client is not None

    # ─── Fallback ─────────────────────────────────────────────────────────────

    @staticmethod
    def _rule_based_fallback(messages: List[Dict]) -> str:
        user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        ).lower()
        if "hello" in user_msg or "hi" in user_msg:
            return "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
        if "time" in user_msg:
            from datetime import datetime
            return f"The current time is {datetime.now().strftime('%I:%M %p')}."
        if "date" in user_msg:
            from datetime import datetime
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
        return "I'm sorry, I don't have an LLM connection. Please configure an API key in your .env file."
