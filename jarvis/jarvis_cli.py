"""
jarvis_cli.py — Jarvis CLI (Text-only mode)
Run Jarvis without any GUI or microphone. 
Useful for testing, remote servers, or Python 3.14 where pyaudio is unavailable.

Usage:
    python jarvis_cli.py
"""

import sys
import logging
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT
from core.engine import JarvisEngine


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    fmt = logging.Formatter(LOG_FORMAT)
    fh  = logging.FileHandler(LOG_FILE, encoding="utf-8")
    sh  = logging.StreamHandler(sys.stdout)
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    sh.setLevel(logging.WARNING)   # Only warnings to console in CLI mode
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))
    root.addHandler(fh)
    root.addHandler(sh)


BANNER = r"""
    ___  ___  ________  ________  ___      ___ ___  ________      
   |\  \|\  \|\   __  \|\   __  \|\  \    /  /|\  \|\   ____\     
   \ \  \ \  \ \  \|\  \ \  \|\  \ \  \  /  / | \  \ \  \___|_    
 __ \ \  \ \  \ \   __  \ \   _  _\ \  \/  / / \ \  \ \_____  \   
|\  \\_\  \ \  \ \  \ \  \ \  \\  \\ \    / /   \ \  \|____|\  \  
\ \________\ \__\ \__\ \__\ \__\\ _\\ \__/ /     \ \__\____\_\  \ 
 \|________|\|__|\|__|\|__|\|__|\|__|\|__|/       \|__|\_________\
                                                        \|_________|
    J.A.R.V.I.S  — Just A Rather Very Intelligent System
    CLI Mode  |  Type 'quit' to exit  |  Type 'help' for commands
"""


def print_colored(text: str, color_code: str = "37") -> None:
    """Print with ANSI color if terminal supports it."""
    print(f"\033[{color_code}m{text}\033[0m")


def main() -> None:
    setup_logging()

    print_colored(BANNER, "96")   # Cyan

    engine = JarvisEngine()

    # Wire CLI callbacks
    def on_state(state: str):
        icons = {"idle": "○", "thinking": "⟳", "speaking": "◉", "error": "✗"}
        icon  = icons.get(state, "○")
        print(f"\r\033[90m[{icon} {state.upper()}]\033[0m", end="", flush=True)

    def on_transcript(role: str, text: str):
        if role == "jarvis":
            print_colored(f"\n  Jarvis: {text}", "95")   # Purple
        elif role == "user":
            pass   # Already printed by input()
        else:
            print_colored(f"\n  [{text}]", "90")

    def on_confirm(message: str) -> bool:
        print_colored(f"\n  ⚠ Confirmation needed: {message}", "93")
        answer = input("  Type 'yes' to confirm, 'no' to cancel: ").strip().lower()
        return answer in ("yes", "y", "haan", "ji")

    engine.on_state_change   = on_state
    engine.on_transcript     = on_transcript
    engine.on_confirm_needed = on_confirm

    print_colored("  Jarvis is ready. Type your command below.\n", "92")

    HELP_TEXT = """
  Available commands:
    open <app>           — Open an application  (e.g. "open chrome")
    open <site>          — Open a website        (e.g. "open youtube")
    search <query>       — Web search
    weather <city>       — Get weather
    tell me about <x>    — Wikipedia lookup
    volume up/down/mute  — System volume
    screenshot           — Take a screenshot
    <any question>       — Chat with Jarvis AI
    help                 — Show this help
    quit / exit          — Exit Jarvis
"""

    while True:
        try:
            print_colored("\n  You: ", "94")
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print_colored("\n  Goodbye.", "96")
            break

        if not raw:
            continue

        if raw.lower() in ("quit", "exit", "bye"):
            print_colored("  Jarvis: Goodbye! Until next time.", "95")
            break

        if raw.lower() == "help":
            print_colored(HELP_TEXT, "90")
            continue

        # Process through engine (blocking in CLI)
        engine.process_input(raw)

    engine.shutdown()


if __name__ == "__main__":
    main()
