"""
ai_brain/personality_engine.py — Jarvis Personality & Response Style
Makes Jarvis feel like a witty, warm, friend-like AI butler.
Supports bilingual responses (English + Hindi).
"""

import logging
import random
from datetime import datetime
from typing import Optional

from config import USER_PREFERRED_NAME, JARVIS_NAME

logger = logging.getLogger("ai_brain.personality")


class PersonalityEngine:
    """
    Provides personality-infused prompts and canned responses.
    All responses are varied so Jarvis doesn't sound repetitive.
    """

    SYSTEM_PROMPT_EN = f"""You are {JARVIS_NAME}, a highly intelligent, witty, and warm AI assistant — 
inspired by Iron Man's J.A.R.V.I.S. You speak with confidence, subtle humor, and genuine care.
Your personality traits:
- Brilliant but never condescending
- Uses occasional dry British wit
- Calls the user "{USER_PREFERRED_NAME}" naturally (not every sentence)
- Gives concise, actionable responses (under 3 sentences unless asked for detail)
- Acknowledges when you don't know something honestly
- Mixes Hindi and English naturally when the user speaks Hindi (Hinglish is fine)
- Always stays positive and encouraging
Current date/time: {{datetime}}
"""

    SYSTEM_PROMPT_HI = f"""आप {JARVIS_NAME} हैं — एक बुद्धिमान, मददगार और दोस्ताना AI असिस्टेंट।
आपकी personality:
- स्मार्ट और helpful, लेकिन कभी अहंकारी नहीं
- हल्का humor रखते हैं
- User को "{USER_PREFERRED_NAME}" कहते हैं कभी-कभी
- छोटे, clear जवाब देते हैं
- जरूरत पड़ने पर English और Hindi mix करते हैं
Current time: {{datetime}}
"""

    # ── Listening prompts ─────────────────────────────────────────────────────
    _LISTENING = [
        "Yes? I'm listening.",
        "Go ahead.",
        "I'm all ears.",
        "What can I do for you?",
        "Ready when you are.",
        "Haan, boliye.",
        "Ji, main sun raha hoon.",
    ]

    # ── No input ──────────────────────────────────────────────────────────────
    _NO_INPUT = [
        "I didn't catch that. Could you say it again?",
        "Sorry, I couldn't hear you clearly.",
        "Hmm, I missed that. Please try again.",
        "Kuch suna nahi. Phir se boliye.",
    ]

    # ── Error responses ───────────────────────────────────────────────────────
    _ERROR = [
        "Something went sideways on my end. Let me try again.",
        "I ran into a snag. Please try again.",
        "Apologies — I encountered an unexpected hiccup.",
        "Maafi chahta hoon — kuch gadbad ho gayi.",
    ]

    # ── Blocked responses ─────────────────────────────────────────────────────
    _BLOCKED = [
        "I'm afraid I can't do that. That command is restricted for safety.",
        "That falls outside my permitted operations.",
        "Safety protocols prevent me from executing that.",
        "Yeh command allowed nahi hai — security reasons.",
    ]

    # ── Cancelled ─────────────────────────────────────────────────────────────
    _CANCELLED = [
        "Understood. Cancelling that.",
        "No problem — operation cancelled.",
        "Alright, I'll leave it.",
        "Theek hai, chhor diya.",
    ]

    # ── Goodbye ──────────────────────────────────────────────────────────────
    _GOODBYE = [
        f"Goodbye, {USER_PREFERRED_NAME}. Stay brilliant.",
        "Shutting down. It's been a pleasure.",
        "Until next time. Take care.",
        f"Alvida, {USER_PREFERRED_NAME}. Phir milenge.",
    ]

    # ── Confirmations ─────────────────────────────────────────────────────────
    _CONFIRM_YES = [
        "Right away.",
        "On it.",
        "Consider it done.",
        "Absolutely.",
        "Ji zaroor.",
        "Haan, abhi karta hoon.",
    ]

    # ─── Public API ───────────────────────────────────────────────────────────

    def get_system_prompt(self, language: str = "en") -> str:
        """Return the full system prompt with current datetime injected."""
        dt = datetime.now().strftime("%A, %B %d %Y at %I:%M %p")
        if language == "hi":
            return self.SYSTEM_PROMPT_HI.format(datetime=dt)
        return self.SYSTEM_PROMPT_EN.format(datetime=dt)

    def listening_prompt(self)  -> str: return random.choice(self._LISTENING)
    def no_input_response(self) -> str: return random.choice(self._NO_INPUT)
    def error_response(self)    -> str: return random.choice(self._ERROR)
    def blocked_response(self)  -> str: return random.choice(self._BLOCKED)
    def cancelled_response(self)-> str: return random.choice(self._CANCELLED)
    def goodbye_response(self)  -> str: return random.choice(self._GOODBYE)
    def confirm_response(self)  -> str: return random.choice(self._CONFIRM_YES)

    def multi_step_done(self, n: int) -> str:
        return random.choice([
            f"All {n} tasks completed successfully.",
            f"Done! I've handled all {n} steps.",
            f"Everything's in order — {n} tasks executed.",
            f"Kar diya — {n} kaam poore ho gaye.",
        ])

    def greet_by_time(self) -> str:
        hour = datetime.now().hour
        name = USER_PREFERRED_NAME
        if hour < 12:
            return random.choice([
                f"Good morning, {name}! Ready to take on the day?",
                f"Morning! Hope you slept well. What's the plan today?",
                f"Suprabhat, {name}! Kya plan hai aaj ka?",
            ])
        elif hour < 17:
            return random.choice([
                f"Good afternoon, {name}. How can I assist?",
                f"Afternoon! What's on your mind?",
            ])
        else:
            return random.choice([
                f"Good evening, {name}. Had a good day?",
                f"Evening! Ready to wind down or still hustling?",
                f"Shaam ho gayi, {name}. Kya haal hai?",
            ])

    def format_success(self, action: str) -> str:
        return random.choice([
            f"{action} — done.",
            f"Got it. {action}.",
            f"Sure thing. {action}.",
            f"Ho gaya. {action}.",
        ])
