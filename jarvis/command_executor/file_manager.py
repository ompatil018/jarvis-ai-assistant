"""
command_executor/file_manager.py — Safe File Operations
Open, search, and delete files with security confirmation.
All destructive operations require explicit confirmation.
"""

import logging
import os
import glob
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("executor.files")

SEARCH_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home(),
]


class FileManager:
    """Handles file open, search, and delete operations."""

    # ─── Open ─────────────────────────────────────────────────────────────────

    def open_file(self, path_or_name: str) -> str:
        """Open a file using the default application."""
        path = self._resolve_path(path_or_name)
        if not path:
            return f"I couldn't find a file matching '{path_or_name}'."

        try:
            logger.info(f"Opening file: {path}")
            os.startfile(str(path))
            return f"Opening '{path.name}'."
        except Exception as exc:
            logger.error(f"File open error: {exc}")
            return f"I couldn't open '{path.name}'. Is it a valid file type?"

    # ─── Search ───────────────────────────────────────────────────────────────

    def search_files(self, query: str) -> str:
        """Search for files matching the query in common directories."""
        if not query.strip():
            return "Please tell me what file to search for."

        results = self._find_files(query, max_results=5)
        if not results:
            return f"No files matching '{query}' found in common directories."

        file_list = "\n".join(f"  • {p}" for p in results)
        return f"Found {len(results)} file(s) matching '{query}':\n{file_list}"

    # ─── Delete ───────────────────────────────────────────────────────────────

    def delete_file(self, path_or_name: str) -> str:
        """
        Delete a file — REQUIRES prior confirmation from security layer.
        This should only be called after PermissionManager.confirm() == True.
        """
        path = self._resolve_path(path_or_name)
        if not path:
            return f"Couldn't find '{path_or_name}' to delete."

        try:
            logger.warning(f"Deleting file: {path}")
            path.unlink()
            return f"'{path.name}' has been deleted."
        except PermissionError:
            return f"Permission denied — couldn't delete '{path.name}'."
        except Exception as exc:
            logger.error(f"Delete error: {exc}")
            return f"Couldn't delete '{path.name}': {exc}"

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _resolve_path(self, path_or_name: str) -> Optional[Path]:
        """Resolve a file by absolute path or by searching common locations."""
        # Absolute path
        p = Path(path_or_name)
        if p.exists():
            return p

        # Search
        results = self._find_files(path_or_name, max_results=1)
        return results[0] if results else None

    def _find_files(self, query: str, max_results: int = 5) -> List[Path]:
        found = []
        for root in SEARCH_ROOTS:
            if not root.exists():
                continue
            for match in root.rglob(f"*{query}*"):
                if match.is_file():
                    found.append(match)
                    if len(found) >= max_results:
                        return found
        return found
