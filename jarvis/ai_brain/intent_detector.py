"""
ai_brain/intent_detector.py — Intent & Entity Classification
Uses LLM to classify user utterances into structured intents.
Falls back to regex rules when LLM is unavailable.
"""

import logging
import json
import re
from typing import Dict, Any

from ai_brain.llm_client import LLMClient
from config import APP_MAPPINGS, WEBSITE_MAPPINGS

logger = logging.getLogger("ai_brain.intent")

INTENT_SYSTEM_PROMPT = """You are an intent classifier for a voice assistant.
Classify the user's utterance into ONE of these intents:
  open_app, open_website, search_web, search_youtube, file_open, file_search,
  file_delete, system_volume, system_screenshot, system_shutdown, system_restart,
  weather, wikipedia, multi_step, general_chat, exit

Return ONLY valid JSON (no markdown):
{
  "intent": "<intent_name>",
  "entities": {
    "app": "<app name if open_app>",
    "site": "<site name if open_website>",
    "query": "<search query if applicable>",
    "path": "<file path if applicable>",
    "city": "<city if weather>",
    "action": "<up|down|mute if volume>",
    "steps": ["<step1>", "<step2>"]
  },
  "confidence": 0.95,
  "language": "en|hi"
}
"""

# ── Regex-based fallback rules ────────────────────────────────────────────────
REGEX_RULES = [
    # Apps
    (re.compile(r"\b(open|launch|start|चालू|खोलो?)\b.+(?P<app>" +
                "|".join(re.escape(a) for a in APP_MAPPINGS) + r")", re.I),
     "open_app", "app"),
    # Websites
    (re.compile(r"\b(open|go to|visit|खोलो?)\b.+(?P<site>" +
                "|".join(re.escape(s) for s in WEBSITE_MAPPINGS) + r")", re.I),
     "open_website", "site"),
    # YouTube search
    (re.compile(r"\bsearch\b.+\bon\b.*(youtube|यूट्यूब)", re.I), "search_youtube", "query"),
    (re.compile(r"\byoutube\b.+\bsearch\b", re.I), "search_youtube", "query"),
    # Web search
    (re.compile(r"\b(search|find|google|look up)\b(?P<query>.+)", re.I), "search_web", "query"),
    # Screenshots
    (re.compile(r"\b(screenshot|screen shot|स्क्रीनशॉट)\b", re.I), "system_screenshot", None),
    # Volume
    (re.compile(r"\b(volume|आवाज़?)\b.+\b(up|increase|बढ़ाओ)\b", re.I), "system_volume", None),
    (re.compile(r"\b(volume|आवाज़?)\b.+\b(down|decrease|घटाओ)\b", re.I), "system_volume", None),
    (re.compile(r"\b(mute|म्यूट)\b", re.I), "system_volume", None),
    # Shutdown / restart
    (re.compile(r"\bshutdown\b|\bshut down\b|\bबंद करो\b", re.I), "system_shutdown", None),
    (re.compile(r"\brestart\b|\breboot\b|\bरीस्टार्ट\b", re.I), "system_restart", None),
    # Weather
    (re.compile(r"\bweather\b|\bमौसम\b", re.I), "weather", "city"),
    # Wikipedia
    (re.compile(r"\bwhat is\b|\bwho is\b|\btell me about\b|\bके बारे में\b", re.I), "wikipedia", "query"),
    # Exit
    (re.compile(r"\b(exit|quit|bye|goodbye|बंद करो)\b.*jarvis", re.I), "exit", None),
    # File ops
    (re.compile(r"\bdelete\b|\bremove\b|\bहटाओ\b", re.I), "file_delete", "path"),
    (re.compile(r"\bopen file\b|\bfile खोलो\b", re.I), "file_open", "path"),
    (re.compile(r"\bsearch file\b|\bfind file\b", re.I), "file_search", "query"),
]


class IntentDetector:
    """Detects user intent using LLM with regex fallback."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def detect(self, text: str) -> Dict[str, Any]:
        """Classify text and return intent dict."""
        if self.llm.is_available():
            result = self._llm_detect(text)
            if result:
                return result

        # Fallback to regex
        return self._regex_detect(text)

    # ─── LLM-based ────────────────────────────────────────────────────────────

    def _llm_detect(self, text: str) -> Dict[str, Any]:
        try:
            messages = [
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user",   "content": text},
            ]
            raw = self.llm.chat(messages, temperature=0.1, max_tokens=250)
            # Strip markdown code fences if present
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
            data = json.loads(raw)
            logger.debug(f"LLM intent: {data}")
            return data
        except Exception as exc:
            logger.warning(f"LLM intent parse error: {exc} — using regex")
            return {}

    # ─── Regex-based fallback ─────────────────────────────────────────────────

    def _regex_detect(self, text: str) -> Dict[str, Any]:
        for pattern, intent, entity_key in REGEX_RULES:
            m = pattern.search(text)
            if m:
                entities = {}
                if entity_key:
                    try:
                        entities[entity_key] = m.group(entity_key).strip()
                    except IndexError:
                        entities[entity_key] = text
                logger.debug(f"Regex intent: {intent}, entities: {entities}")
                return {"intent": intent, "entities": entities, "confidence": 0.7}

        # Check direct app/site name mentions
        lower = text.lower()
        for app in APP_MAPPINGS:
            if app in lower:
                return {"intent": "open_app", "entities": {"app": app}, "confidence": 0.6}
        for site in WEBSITE_MAPPINGS:
            if site in lower:
                return {"intent": "open_website", "entities": {"site": site}, "confidence": 0.6}

        return {"intent": "general_chat", "entities": {}, "confidence": 0.5}
