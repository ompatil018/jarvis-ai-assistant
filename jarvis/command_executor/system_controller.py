"""
command_executor/system_controller.py — System Automation
Volume control, screenshots, shutdown, restart — all with safety checks.
"""

import logging
import os
import subprocess
import platform
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("executor.system")

SCREENSHOTS_DIR = Path.home() / "Pictures" / "Jarvis Screenshots"


class SystemController:
    """Controls system-level operations on Windows."""

    # ─── Volume ───────────────────────────────────────────────────────────────

    def adjust_volume(self, action: str) -> str:
        """Adjust system volume: up | down | mute."""
        action = action.lower().strip()
        try:
            if action in ("up", "increase", "बढ़ाओ"):
                # Use PowerShell to increase volume by 10%
                self._ps(
                    "$obj = New-Object -ComObject WScript.Shell; "
                    "1..2 | ForEach-Object { $obj.SendKeys([char]175) }"
                )
                return "Volume turned up."

            elif action in ("down", "decrease", "घटाओ"):
                self._ps(
                    "$obj = New-Object -ComObject WScript.Shell; "
                    "1..2 | ForEach-Object { $obj.SendKeys([char]174) }"
                )
                return "Volume turned down."

            elif action in ("mute", "म्यूट"):
                self._ps(
                    "$obj = New-Object -ComObject WScript.Shell; "
                    "$obj.SendKeys([char]173)"
                )
                return "Volume muted."

            else:
                return f"Unknown volume action: '{action}'."

        except Exception as exc:
            logger.error(f"Volume error: {exc}")
            return "Couldn't adjust the volume."

    # ─── Screenshot ───────────────────────────────────────────────────────────

    def take_screenshot(self) -> str:
        """Capture a full-screen screenshot and save it."""
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = SCREENSHOTS_DIR / f"jarvis_{ts}.png"

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
            return f"Screenshot saved as '{filepath.name}'."
        except ImportError:
            # Fallback: Windows Snipping Tool
            subprocess.Popen(["SnippingTool.exe"])
            return "Opening Snipping Tool for you."
        except Exception as exc:
            logger.error(f"Screenshot error: {exc}")
            return "Couldn't take a screenshot."

    # ─── Power Operations (Require Confirmation) ──────────────────────────────

    def shutdown(self) -> str:
        """Schedule system shutdown in 60 seconds."""
        try:
            logger.warning("Initiating shutdown in 60 seconds.")
            subprocess.run(["shutdown", "/s", "/t", "60"], check=True)
            return "System will shut down in 60 seconds. Say 'cancel shutdown' to abort."
        except Exception as exc:
            logger.error(f"Shutdown error: {exc}")
            return "Couldn't initiate shutdown."

    def cancel_shutdown(self) -> str:
        try:
            subprocess.run(["shutdown", "/a"], check=True)
            return "Shutdown cancelled."
        except Exception:
            return "No pending shutdown to cancel."

    def restart(self) -> str:
        try:
            logger.warning("Initiating restart in 60 seconds.")
            subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
            return "System will restart in 60 seconds."
        except Exception as exc:
            logger.error(f"Restart error: {exc}")
            return "Couldn't initiate restart."

    def lock_screen(self) -> str:
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "Screen locked."
        except Exception:
            return "Couldn't lock the screen."

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _ps(command: str) -> None:
        """Run a PowerShell snippet."""
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", command],
            capture_output=True,
        )
