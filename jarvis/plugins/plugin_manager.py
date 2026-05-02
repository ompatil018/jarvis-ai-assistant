"""
plugins/plugin_manager.py — Dynamic Plugin System
Discovers and loads plugins from the plugins/ directory.
Each plugin registers intents and handlers, extending Jarvis's capabilities.

Plugin API:
  Each plugin must implement:
    - PLUGIN_NAME: str
    - PLUGIN_INTENTS: list[str]
    - handle(intent, entities, raw_text) -> str | None
"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, List, Any, TYPE_CHECKING

from config import PLUGINS_DIR

if TYPE_CHECKING:
    from core.engine import JarvisEngine

logger = logging.getLogger("plugins.manager")


class PluginManager:
    """Discovers, loads, and dispatches to Jarvis plugins."""

    def __init__(self, engine: "JarvisEngine") -> None:
        self.engine  = engine
        self._plugins: Dict[str, Any] = {}   # intent → plugin module

    def load_all(self) -> None:
        """Scan PLUGINS_DIR for plugin subdirectories and load them."""
        if not PLUGINS_DIR.exists():
            return

        for entry in PLUGINS_DIR.iterdir():
            if entry.is_dir() and (entry / "plugin.py").exists():
                self._load_plugin(entry)

        logger.info(f"Loaded {len(self._plugins)} plugin intent mappings from {PLUGINS_DIR}")

    def _load_plugin(self, plugin_dir: Path) -> None:
        """Load a single plugin from its directory."""
        plugin_path = plugin_dir / "plugin.py"
        try:
            spec   = importlib.util.spec_from_file_location(
                f"plugins.{plugin_dir.name}.plugin", plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            name    = getattr(module, "PLUGIN_NAME",    plugin_dir.name)
            intents = getattr(module, "PLUGIN_INTENTS", [])

            for intent in intents:
                self._plugins[intent] = module
                logger.info(f"  Plugin '{name}' registered intent: {intent}")

        except Exception as exc:
            logger.error(f"Failed to load plugin from {plugin_dir}: {exc}")

    def handle(self, intent: str, entities: dict, raw_text: str) -> Optional[str]:
        """Dispatch to a plugin that handles the given intent. Returns None if no match."""
        if intent in self._plugins:
            module = self._plugins[intent]
            try:
                return module.handle(intent, entities, raw_text)
            except Exception as exc:
                logger.error(f"Plugin handle error for intent '{intent}': {exc}")
        return None

    def list_plugins(self) -> List[str]:
        """Return list of registered plugin names."""
        names = set()
        for module in self._plugins.values():
            names.add(getattr(module, "PLUGIN_NAME", "unknown"))
        return list(names)
