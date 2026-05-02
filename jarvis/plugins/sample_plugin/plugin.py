"""
plugins/sample_plugin/plugin.py — Sample Plugin Template
Demonstrates how to create a Jarvis plugin.

To create your own plugin:
1. Create a new folder in plugins/ (e.g., plugins/my_plugin/)
2. Copy this file as plugin.py
3. Set PLUGIN_NAME and PLUGIN_INTENTS
4. Implement the handle() function
5. Jarvis will auto-discover and load it at startup
"""

import logging
from typing import Optional

logger = logging.getLogger("plugins.sample")

# ── Required plugin metadata ──────────────────────────────────────────────────
PLUGIN_NAME    = "SamplePlugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_INTENTS = ["tell_joke", "flip_coin", "roll_dice"]

# ── Plugin logic ──────────────────────────────────────────────────────────────

import random

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? He was outstanding in his field.",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I asked the AI if it dreams. It said it prefers batch processing.",
]


def handle(intent: str, entities: dict, raw_text: str) -> Optional[str]:
    """Handle intents registered by this plugin."""

    if intent == "tell_joke":
        return random.choice(JOKES)

    elif intent == "flip_coin":
        result = random.choice(["Heads", "Tails"])
        return f"I flipped a coin — it's {result}!"

    elif intent == "roll_dice":
        sides = entities.get("sides", 6)
        try:
            sides = int(sides)
        except (ValueError, TypeError):
            sides = 6
        result = random.randint(1, sides)
        return f"I rolled a {sides}-sided die — you got {result}!"

    return None
