"""
command_executor/browser_controller.py — Browser & Web Navigation
Opens URLs, performs Google/YouTube searches, and navigates websites.
"""

import logging
import urllib.parse
import webbrowser
from typing import Optional

from config import WEBSITE_MAPPINGS

logger = logging.getLogger("executor.browser")


class BrowserController:
    """Controls the default web browser."""

    def open(self, site_name: str) -> str:
        """Open a named website or a raw URL."""
        site_name = site_name.strip().lower()

        # Direct URL
        if site_name.startswith(("http://", "https://", "www.")):
            url = site_name if site_name.startswith("http") else f"https://{site_name}"
            self._navigate(url)
            return f"Opening {url}."

        # Exact match
        if site_name in WEBSITE_MAPPINGS:
            url = WEBSITE_MAPPINGS[site_name]
            self._navigate(url)
            return f"Opening {site_name.capitalize()}."

        # Fuzzy match
        for key, url in WEBSITE_MAPPINGS.items():
            if key in site_name or site_name in key:
                self._navigate(url)
                return f"Opening {key.capitalize()}."

        # Google search fallback
        return self.google_search(site_name)

    def google_search(self, query: str) -> str:
        """Open Google search for the given query."""
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        self._navigate(url)
        return f"Searching Google for '{query}'."

    def search_youtube(self, query: str) -> str:
        """Search YouTube for the given query."""
        if not query:
            self._navigate("https://www.youtube.com")
            return "Opening YouTube."
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        self._navigate(url)
        return f"Searching YouTube for '{query}'."

    def open_url(self, url: str) -> str:
        """Directly open any URL."""
        self._navigate(url)
        return f"Navigating to {url}."

    @staticmethod
    def _navigate(url: str) -> None:
        logger.info(f"Browser opening: {url}")
        webbrowser.open(url, new=2)
