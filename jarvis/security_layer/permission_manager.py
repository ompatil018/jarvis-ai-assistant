"""
security_layer/permission_manager.py — Confirmation & Permission Dialogs
Provides GUI and voice-based confirmation prompts for destructive operations.
"""

import logging
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable

logger = logging.getLogger("security.permissions")


class PermissionManager:
    """Handles user confirmation for sensitive operations."""

    def __init__(self) -> None:
        self._gui_available = True   # will be set to False if Tk fails

    def confirm_gui(self, message: str, title: str = "Jarvis — Confirmation Required") -> bool:
        """Show a modal confirmation dialog. Returns True if user clicks Yes."""
        result = {"value": False}

        def _show():
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                answer = messagebox.askyesno(title, message, parent=root)
                result["value"] = bool(answer)
                root.destroy()
            except Exception as exc:
                logger.error(f"GUI confirm error: {exc}")
                result["value"] = False

        # Must run on main thread or a dedicated Tk thread
        if threading.current_thread() is threading.main_thread():
            _show()
        else:
            t = threading.Thread(target=_show)
            t.start()
            t.join(timeout=30)

        logger.info(f"Confirmation for '{message[:50]}': {result['value']}")
        return result["value"]

    def confirm_voice_callback(
        self,
        message: str,
        tts_speak: Callable[[str], None],
        listen_fn:  Callable[[], str],
    ) -> bool:
        """Ask for confirmation via voice (speak + listen for yes/no)."""
        tts_speak(f"{message} Say yes to confirm, or no to cancel.")
        answer = listen_fn()
        if not answer:
            return False
        confirmed = any(
            word in answer.lower()
            for word in ["yes", "yeah", "confirm", "sure", "okay", "ok", "हाँ", "haan", "ji"]
        )
        logger.info(f"Voice confirmation for '{message[:50]}': {confirmed}")
        return confirmed

    def require_admin_check(self) -> bool:
        """Check if process is running with admin privileges (Windows)."""
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
