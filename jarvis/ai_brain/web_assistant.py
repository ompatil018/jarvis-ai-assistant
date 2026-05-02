"""
ai_brain/web_assistant.py — Web Search, Weather & Wikipedia
Provides Jarvis with internet capabilities:
  - DuckDuckGo search (no API key needed)
  - Wikipedia summaries
  - OpenWeatherMap weather (optional API key)
  - News headlines (Google News RSS)
"""

import logging
import re
import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import OPENWEATHER_KEY

logger = logging.getLogger("ai_brain.web")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JarvisAI/1.0"}
TIMEOUT = 8


class WebAssistant:
    """Performs web lookups for Jarvis responses."""

    # ─── DuckDuckGo Search ────────────────────────────────────────────────────

    def search(self, query: str) -> str:
        """Search DuckDuckGo and return a brief answer."""
        if not query.strip():
            return "Please give me something to search for."
        try:
            # DuckDuckGo instant answer API
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
            resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            abstract = data.get("AbstractText", "").strip()
            if abstract:
                return f"{abstract[:400]}."

            answer = data.get("Answer", "").strip()
            if answer:
                return answer

            # Fallback: scrape first result snippet
            return self._scrape_snippet(query)

        except Exception as exc:
            logger.error(f"Search error: {exc}")
            return f"I couldn't find results for '{query}'. Please try rephrasing."

    def _scrape_snippet(self, query: str) -> str:
        try:
            url     = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp    = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            soup    = BeautifulSoup(resp.text, "html.parser")
            snippet = soup.find("a", class_="result__snippet")
            if snippet:
                return snippet.get_text(strip=True)[:300]
        except Exception:
            pass
        return f"I searched for '{query}' but couldn't retrieve a clean result."

    # ─── Wikipedia ────────────────────────────────────────────────────────────

    def wikipedia_summary(self, query: str) -> str:
        """Fetch a Wikipedia summary for the query."""
        if not query.strip():
            return "What would you like to know about?"
        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia(
                language="en",
                user_agent="JarvisAI/1.0"
            )
            page = wiki.page(query)
            if page.exists():
                summary = page.summary[:500]
                return f"{summary}... Would you like more details?"
            else:
                # Try requests fallback
                return self._wikipedia_api_fallback(query)
        except ImportError:
            return self._wikipedia_api_fallback(query)
        except Exception as exc:
            logger.error(f"Wikipedia error: {exc}")
            return f"I couldn't find Wikipedia information about '{query}'."

    def _wikipedia_api_fallback(self, query: str) -> str:
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + \
                  urllib.parse.quote(query.replace(" ", "_"))
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                data    = resp.json()
                extract = data.get("extract", "")
                if extract:
                    return f"{extract[:450]}."
        except Exception:
            pass
        return f"No Wikipedia article found for '{query}'."

    # ─── Weather ──────────────────────────────────────────────────────────────

    def get_weather(self, city: str = "") -> str:
        """Get weather using OpenWeatherMap API."""
        if not city:
            city = "Mumbai"   # Default

        if OPENWEATHER_KEY:
            return self._weather_owm(city)
        else:
            return self._weather_wttr(city)

    def _weather_owm(self, city: str) -> str:
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": OPENWEATHER_KEY, "units": "metric"}
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data    = resp.json()
            temp    = data["main"]["temp"]
            desc    = data["weather"][0]["description"].capitalize()
            humidity= data["main"]["humidity"]
            return (
                f"In {city}, it's currently {temp:.1f}°C with {desc}. "
                f"Humidity is {humidity}%."
            )
        except Exception as exc:
            logger.error(f"OWM weather error: {exc}")
            return self._weather_wttr(city)

    def _weather_wttr(self, city: str) -> str:
        """Use wttr.in (no API key needed)."""
        try:
            url  = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            text = resp.text.strip()
            return f"Weather for {text}."
        except Exception as exc:
            logger.error(f"wttr.in error: {exc}")
            return f"I couldn't retrieve weather for {city} right now."

    # ─── News ─────────────────────────────────────────────────────────────────

    def get_news_headlines(self, n: int = 5) -> str:
        """Fetch top headlines from Google News RSS."""
        try:
            url  = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            soup  = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")[:n]
            headlines = [re.sub(r"\s*-\s*\S+$", "", item.title.text) for item in items]
            if headlines:
                numbered = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
                return f"Here are today's top {len(headlines)} headlines:\n{numbered}"
        except Exception as exc:
            logger.error(f"News fetch error: {exc}")
        return "I couldn't fetch the news right now."
