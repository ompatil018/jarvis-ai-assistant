"""
ai_brain/response_generator.py — LLM Prompt Builder & Response Generator
Builds contextual prompts using memory, personality, and context, then
calls the LLM to generate a final response.
"""

import logging
from typing import TYPE_CHECKING

from ai_brain.llm_client import LLMClient
from ai_brain.conversation_memory import ConversationMemory
from ai_brain.personality_engine import PersonalityEngine

if TYPE_CHECKING:
    from ai_brain.context_engine import ContextEngine

logger = logging.getLogger("ai_brain.response_gen")


def _detect_language(text: str) -> str:
    """Heuristic: Devanagari chars → Hindi."""
    hi_chars = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    return "hi" if hi_chars > len(text) * 0.1 else "en"


class ResponseGenerator:
    """Generates contextual LLM responses with memory and personality."""

    def __init__(
        self,
        llm:         LLMClient,
        memory:      ConversationMemory,
        personality: PersonalityEngine,
        context:     "ContextEngine",
    ) -> None:
        self.llm         = llm
        self.memory      = memory
        self.personality = personality
        self.context     = context

    def generate(self, user_text: str) -> str:
        """Generate a response for general chat."""
        lang = _detect_language(user_text)

        # Build messages list
        system_prompt = self.personality.get_system_prompt(lang)

        # Inject context awareness
        ctx_block = self.context.get_context_block()
        if ctx_block:
            system_prompt += f"\n\nCurrent system context:\n{ctx_block}"

        # Check memory for relevant past info
        relevant = self.memory.search_memory(user_text, top_k=2)
        if relevant:
            memory_block = "\n".join(f"- {r}" for r in relevant)
            system_prompt += f"\n\nRelevant memory:\n{memory_block}"

        messages = [{"role": "system", "content": system_prompt}]
        messages += self.memory.get_context_messages(last_n=10)
        messages.append({"role": "user", "content": user_text})

        response = self.llm.chat(messages)

        # Trigger summarization if needed
        if self.memory.should_summarize():
            self._summarize_async()

        return response

    def _summarize_async(self) -> None:
        """Ask LLM to summarize older conversation turns."""
        import threading
        threading.Thread(target=self._summarize, daemon=True).start()

    def _summarize(self) -> None:
        try:
            turns = self.memory.get_context_messages(last_n=20)
            if not turns:
                return
            conv_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in turns
            )
            messages = [
                {"role": "system", "content":
                    "Summarize the following conversation in 2-3 sentences, "
                    "focusing on key facts, user preferences, and actions taken."},
                {"role": "user", "content": conv_text},
            ]
            summary = self.llm.chat(messages, max_tokens=150)
            self.memory.set_summary(summary)
            logger.info(f"Memory summarized: {summary[:80]}...")
        except Exception as exc:
            logger.error(f"Summarization error: {exc}")
