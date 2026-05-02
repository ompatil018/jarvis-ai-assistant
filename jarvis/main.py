"""
main.py — Jarvis AI Desktop Assistant Entry Point
Bootstraps all systems and launches the futuristic GUI.
"""

import sys
import logging
import threading
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent))

from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT
from core.engine import JarvisEngine
from gui.main_window import JarvisGUI


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    fmt = logging.Formatter(LOG_FORMAT)

    file_handler   = logging.FileHandler(LOG_FILE, encoding="utf-8")
    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler.setFormatter(fmt)
    stream_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))
    root.addHandler(file_handler)
    root.addHandler(stream_handler)


def main() -> None:
    setup_logging()
    logger = logging.getLogger("main")
    logger.info("=" * 65)
    logger.info("  J.A.R.V.I.S  —  Just A Rather Very Intelligent System")
    logger.info("=" * 65)

    engine = JarvisEngine()

    # Engine runs its background loops on daemon threads
    engine_thread = threading.Thread(target=engine.start, daemon=True, name="JarvisEngine")
    engine_thread.start()

    # GUI blocks the main thread until the window is closed
    gui = JarvisGUI(engine)
    gui.run()

    # Clean shutdown
    engine.shutdown()
    logger.info("Jarvis has shut down. Goodbye.")


if __name__ == "__main__":
    main()
