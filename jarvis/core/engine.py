"""
core/engine.py — Main Jarvis Orchestrator
Coordinates all modules: voice, AI brain, command executor, security, plugins.
"""

import logging
import threading
import queue
from typing import Optional, Callable

from voice_module.speech_recognizer import SpeechRecognizer
from voice_module.text_to_speech import TextToSpeech
from voice_module.wake_word import WakeWordDetector
from voice_module.listening_mode import ListeningMode
from ai_brain.llm_client import LLMClient
from ai_brain.intent_detector import IntentDetector
from ai_brain.conversation_memory import ConversationMemory
from ai_brain.response_generator import ResponseGenerator
from ai_brain.personality_engine import PersonalityEngine
from ai_brain.suggestion_engine import SuggestionEngine
from ai_brain.context_engine import ContextEngine
from ai_brain.web_assistant import WebAssistant
from command_executor.app_launcher import AppLauncher
from command_executor.browser_controller import BrowserController
from command_executor.file_manager import FileManager
from command_executor.system_controller import SystemController
from security_layer.command_validator import CommandValidator
from security_layer.permission_manager import PermissionManager
from core.task_engine import TaskEngine
from plugins.plugin_manager import PluginManager
from ai_brain.user_profile_manager import UserProfileManager

logger = logging.getLogger("core.engine")


class JarvisEngine:
    """Central orchestrator that wires all Jarvis subsystems together."""

    def __init__(self) -> None:
        logger.info("Initializing Jarvis Engine...")

        # ── Queues for inter-thread communication ─────────────────────────────
        self.input_queue:    queue.Queue = queue.Queue()
        self.output_queue:   queue.Queue = queue.Queue()
        self._running = False
        self._shutdown_event = threading.Event()

        # ── GUI callback (set by GUI after init) ──────────────────────────────
        self.on_state_change:   Optional[Callable] = None   # (state: str) → None
        self.on_transcript:     Optional[Callable] = None   # (role, text) → None
        self.on_suggestion:     Optional[Callable] = None   # (suggestions) → None
        self.on_confirm_needed: Optional[Callable] = None   # (msg) → bool

        # ── Subsystems ────────────────────────────────────────────────────────
        self.tts          = TextToSpeech()
        self.stt          = SpeechRecognizer()
        self.wake_word    = WakeWordDetector()
        self.listen_mode  = ListeningMode(self.stt, self.wake_word)

        self.memory       = ConversationMemory()
        self.personality  = PersonalityEngine()
        self.context      = ContextEngine()
        self.llm          = LLMClient()
        self.intent       = IntentDetector(self.llm)
        self.response_gen = ResponseGenerator(self.llm, self.memory, self.personality, self.context)
        self.suggestions  = SuggestionEngine(self.memory, self.context)
        self.web          = WebAssistant()

        self.app_launcher = AppLauncher()
        self.browser      = BrowserController()
        self.file_mgr     = FileManager()
        self.sys_ctrl     = SystemController()

        self.validator    = CommandValidator()
        self.permissions  = PermissionManager()

        self.task_engine  = TaskEngine(self)
        self.plugins      = PluginManager(self)
        self.plugins.load_all()
        self.user_profile = UserProfileManager()

        logger.info("Jarvis Engine initialized successfully.")

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Entry point for the engine's background thread."""
        self._running = True
        logger.info("Engine started — listening for wake word...")
        self._set_state("idle")
        self._main_loop()

    def shutdown(self) -> None:
        """Signal a clean shutdown."""
        logger.info("Shutting down engine...")
        self._running = False
        self._shutdown_event.set()
        self.listen_mode.stop()

    # ─── Main Loop ────────────────────────────────────────────────────────────

    def _main_loop(self) -> None:
        while self._running and not self._shutdown_event.is_set():
            try:
                # 1. Wait for wake word
                self._set_state("idle")
                detected = self.listen_mode.wait_for_wake_word(
                    shutdown_event=self._shutdown_event
                )
                if not detected:
                    continue

                # 2. Acknowledge
                self._set_state("listening")
                greeting = self.personality.listening_prompt()
                self._speak(greeting)
                self._emit_transcript("jarvis", greeting)

                # 3. Listen for command (with interrupt support)
                user_text = self.listen_mode.listen_for_command()
                if not user_text or user_text.strip() == "":
                    self._speak(self.personality.no_input_response())
                    continue

                logger.info(f"User said: {user_text}")
                self._emit_transcript("user", user_text)
                self._set_state("thinking")

                # 4. Process command
                self.process_input(user_text)

            except Exception as exc:
                logger.exception(f"Engine loop error: {exc}")
                self._set_state("error")

    # ─── Command Processing ───────────────────────────────────────────────────

    def process_input(self, user_text: str) -> None:
        """Full pipeline: security → intent → execute / LLM → respond."""
        try:
            # Security check
            if not self.validator.is_safe(user_text):
                warning = self.personality.blocked_response()
                self._speak(warning)
                self._emit_transcript("jarvis", warning)
                return

            # Update context
            self.context.update(user_text)

            # Detect intent
            intent_data = self.intent.detect(user_text)
            intent      = intent_data.get("intent", "general_chat")
            entities    = intent_data.get("entities", {})
            logger.info(f"Intent: {intent} | Entities: {entities}")

            # Check if confirmation required
            if self.validator.requires_confirmation(user_text):
                confirmed = self._request_confirmation(
                    f"Are you sure you want to: {user_text}?"
                )
                if not confirmed:
                    resp = self.personality.cancelled_response()
                    self._speak(resp)
                    self._emit_transcript("jarvis", resp)
                    return

            # Route to handler
            response = self._route_intent(intent, entities, user_text)

            # Save to memory & update profile
            self.memory.add_turn("user", user_text)
            self.memory.add_turn("assistant", response)
            self.user_profile.record_interaction(user_text)
            # Track favorites
            if intent == "open_app":
                self.user_profile.add_favorite_app(entities.get("app", ""))
            elif intent == "open_website":
                self.user_profile.add_favorite_site(entities.get("site", ""))

            # Speak & display response
            self._speak(response)
            self._emit_transcript("jarvis", response)
            self._set_state("idle")

            # Generate suggestions asynchronously
            threading.Thread(
                target=self._push_suggestions, daemon=True
            ).start()

        except Exception as exc:
            logger.exception(f"process_input error: {exc}")
            err_msg = self.personality.error_response()
            self._speak(err_msg)
            self._emit_transcript("jarvis", err_msg)
            self._set_state("idle")

    def _route_intent(self, intent: str, entities: dict, raw_text: str) -> str:
        """Dispatch to the correct handler based on detected intent."""

        # Check plugins first
        plugin_resp = self.plugins.handle(intent, entities, raw_text)
        if plugin_resp:
            return plugin_resp

        if intent == "open_app":
            app_name = entities.get("app", raw_text)
            return self.app_launcher.launch(app_name)

        elif intent == "open_website":
            site = entities.get("site", raw_text)
            return self.browser.open(site)

        elif intent == "search_web":
            query = entities.get("query", raw_text)
            result = self.web.search(query)
            return result

        elif intent == "search_youtube":
            query = entities.get("query", "")
            return self.browser.search_youtube(query)

        elif intent == "file_open":
            path = entities.get("path", "")
            return self.file_mgr.open_file(path)

        elif intent == "file_search":
            query = entities.get("query", "")
            return self.file_mgr.search_files(query)

        elif intent == "file_delete":
            path = entities.get("path", "")
            return self.file_mgr.delete_file(path)

        elif intent == "system_volume":
            action = entities.get("action", "up")
            return self.sys_ctrl.adjust_volume(action)

        elif intent == "system_screenshot":
            return self.sys_ctrl.take_screenshot()

        elif intent == "system_shutdown":
            return self.sys_ctrl.shutdown()

        elif intent == "system_restart":
            return self.sys_ctrl.restart()

        elif intent == "weather":
            city = entities.get("city", "")
            return self.web.get_weather(city)

        elif intent == "wikipedia":
            query = entities.get("query", raw_text)
            return self.web.wikipedia_summary(query)

        elif intent == "multi_step":
            steps = entities.get("steps", [])
            return self.task_engine.execute_multi_step(steps)

        elif intent == "exit":
            self.shutdown()
            return self.personality.goodbye_response()

        else:
            # Fallback to LLM general chat
            return self.response_gen.generate(raw_text)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _speak(self, text: str) -> None:
        self._set_state("speaking")
        self.tts.speak(text)

    def _set_state(self, state: str) -> None:
        if self.on_state_change:
            self.on_state_change(state)

    def _emit_transcript(self, role: str, text: str) -> None:
        if self.on_transcript:
            self.on_transcript(role, text)

    def _push_suggestions(self) -> None:
        try:
            suggestions = self.suggestions.get_suggestions()
            if suggestions and self.on_suggestion:
                self.on_suggestion(suggestions)
        except Exception:
            pass

    def _request_confirmation(self, message: str) -> bool:
        """Ask user for confirmation — via GUI callback or TTS."""
        if self.on_confirm_needed:
            return self.on_confirm_needed(message)
        # Fallback: voice confirmation
        self._speak(f"{message} Say yes or no.")
        answer = self.listen_mode.listen_for_command()
        return answer and "yes" in answer.lower()
