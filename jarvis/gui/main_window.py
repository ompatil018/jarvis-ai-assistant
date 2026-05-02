"""
gui/main_window.py — Jarvis Futuristic Main Window
A dark, Jarvis-style Tkinter interface featuring:
  - Animated orb with state-aware colors
  - Scrollable bilingual transcript panel
  - Waveform listening indicator
  - Smart suggestion chips
  - System stats bar
  - Manual input field (type commands when mic isn't available)
"""

import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime
from typing import TYPE_CHECKING, List

from gui.widgets import (
    AnimatedOrb, WaveformBar, LEDIndicator,
    SuggestionChip, COLORS
)

if TYPE_CHECKING:
    from core.engine import JarvisEngine


class JarvisGUI:
    """Main Jarvis application window."""

    WINDOW_TITLE = "J.A.R.V.I.S  —  AI Desktop Assistant"
    MIN_W, MIN_H = 860, 640

    def __init__(self, engine: "JarvisEngine") -> None:
        self.engine = engine
        self._root  = tk.Tk()
        self._setup_window()
        self._build_ui()
        self._wire_engine()

    # ─── Window Setup ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        r = self._root
        r.title(self.WINDOW_TITLE)
        r.configure(bg=COLORS["bg"])
        r.minsize(self.MIN_W, self.MIN_H)
        r.resizable(True, True)

        # Center window
        sw = r.winfo_screenwidth()
        sh = r.winfo_screenheight()
        x  = (sw - self.MIN_W) // 2
        y  = (sh - self.MIN_H) // 2
        r.geometry(f"{self.MIN_W}x{self.MIN_H}+{x}+{y}")

        # Window icon / taskbar title
        try:
            r.iconbitmap(default="")   # blank to avoid error
        except Exception:
            pass

        r.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI Builder ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = self._root

        # ── Top Bar ───────────────────────────────────────────────────────────
        top_bar = tk.Frame(root, bg=COLORS["panel"], height=50)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        tk.Label(
            top_bar, text="⬡  J.A.R.V.I.S",
            bg=COLORS["panel"], fg=COLORS["accent"],
            font=("Consolas", 15, "bold"), padx=20
        ).pack(side=tk.LEFT, pady=8)

        self._time_label = tk.Label(
            top_bar, text="", bg=COLORS["panel"],
            fg=COLORS["text_secondary"], font=("Consolas", 10)
        )
        self._time_label.pack(side=tk.RIGHT, padx=20)
        self._update_clock()

        # ── Main Body ─────────────────────────────────────────────────────────
        body = tk.Frame(root, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left: Orb + status
        left = tk.Frame(body, bg=COLORS["bg"], width=240)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        left.pack_propagate(False)
        self._build_orb_panel(left)

        # Right: Transcript + input
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._build_transcript_panel(right)
        self._build_suggestion_panel(right)
        self._build_input_panel(right)

        # ── Status Bar ────────────────────────────────────────────────────────
        self._build_status_bar(root)

    def _build_orb_panel(self, parent: tk.Frame) -> None:
        tk.Label(
            parent, text="CORE STATUS", bg=COLORS["bg"],
            fg=COLORS["text_secondary"], font=("Consolas", 8)
        ).pack(pady=(10, 0))

        # Orb
        self._orb = AnimatedOrb(parent, size=200, bg=COLORS["bg"])
        self._orb.pack(pady=10)

        # Waveform
        self._waveform = WaveformBar(parent, width=200, height=36)
        self._waveform.pack(pady=4)

        # LED Indicators
        led_frame = tk.Frame(parent, bg=COLORS["bg"])
        led_frame.pack(pady=8)
        self._led_mic    = LEDIndicator(led_frame, "Microphone", bg=COLORS["bg"])
        self._led_ai     = LEDIndicator(led_frame, "AI Engine",  bg=COLORS["bg"])
        self._led_memory = LEDIndicator(led_frame, "Memory",     bg=COLORS["bg"])
        for led in (self._led_mic, self._led_ai, self._led_memory):
            led.pack(anchor="w", padx=10, pady=1)

        # Mic toggle button
        self._mic_btn = tk.Button(
            parent, text="🎤  Hold to Speak",
            bg=COLORS["glow"], fg=COLORS["accent"],
            font=("Segoe UI", 10, "bold"),
            activebackground=COLORS["accent"], activeforeground=COLORS["bg"],
            relief="flat", padx=16, pady=8, cursor="hand2",
            command=self._on_mic_toggle
        )
        self._mic_btn.pack(pady=12, padx=15, fill=tk.X)

        self._mic_active = False

    def _build_transcript_panel(self, parent: tk.Frame) -> None:
        tk.Label(
            parent, text="CONVERSATION LOG", bg=COLORS["bg"],
            fg=COLORS["text_secondary"], font=("Consolas", 8)
        ).pack(anchor="w", padx=4, pady=(6, 2))

        # Bordered frame
        border = tk.Frame(parent, bg=COLORS["border"], bd=1, relief="flat")
        border.pack(fill=tk.BOTH, expand=True, padx=4)

        self._transcript = scrolledtext.ScrolledText(
            border,
            bg=COLORS["panel"], fg=COLORS["text_primary"],
            font=("Segoe UI", 10), wrap=tk.WORD,
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent"],
            relief="flat", bd=0, padx=12, pady=8,
            state=tk.DISABLED,
        )
        self._transcript.pack(fill=tk.BOTH, expand=True)

        # Text tags
        self._transcript.tag_configure("user",   foreground=COLORS["text_user"],   font=("Segoe UI", 10, "bold"))
        self._transcript.tag_configure("jarvis", foreground=COLORS["text_jarvis"], font=("Segoe UI", 10))
        self._transcript.tag_configure("system", foreground=COLORS["text_secondary"], font=("Segoe UI", 9, "italic"))
        self._transcript.tag_configure("time",   foreground=COLORS["border"],      font=("Consolas", 8))

    def _build_suggestion_panel(self, parent: tk.Frame) -> None:
        self._suggestion_frame = tk.Frame(parent, bg=COLORS["bg"])
        self._suggestion_frame.pack(fill=tk.X, padx=4, pady=4)
        self._suggestion_chips: list = []

    def _build_input_panel(self, parent: tk.Frame) -> None:
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill=tk.X, padx=4, pady=(2, 6))

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            frame, textvariable=self._input_var,
            bg=COLORS["panel"], fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            font=("Segoe UI", 11),
            relief="flat", bd=0,
        )
        self._input_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True,
            ipady=10, padx=(8, 4)
        )
        self._input_entry.bind("<Return>", self._on_enter_pressed)

        send_btn = tk.Button(
            frame, text="➤ Send",
            bg=COLORS["accent"], fg=COLORS["bg"],
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=14, pady=8,
            cursor="hand2", command=self._on_send_text
        )
        send_btn.pack(side=tk.RIGHT, padx=4)

        # Placeholder
        self._input_entry.insert(0, "Type a command or question...")
        self._input_entry.config(fg=COLORS["text_secondary"])
        self._input_entry.bind("<FocusIn>",  self._on_entry_focus_in)
        self._input_entry.bind("<FocusOut>", self._on_entry_focus_out)

    def _build_status_bar(self, root: tk.Tk) -> None:
        bar = tk.Frame(root, bg=COLORS["panel"], height=28)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self._status_label = tk.Label(
            bar, text="● STANDBY",
            bg=COLORS["panel"], fg=COLORS["text_secondary"],
            font=("Consolas", 9), padx=16
        )
        self._status_label.pack(side=tk.LEFT, pady=4)

        tk.Label(
            bar, text="Say 'Hey Jarvis' to activate",
            bg=COLORS["panel"], fg=COLORS["text_secondary"],
            font=("Segoe UI", 8)
        ).pack(side=tk.RIGHT, padx=16)

    # ─── Engine Wiring ────────────────────────────────────────────────────────

    def _wire_engine(self) -> None:
        """Connect engine callbacks to GUI update methods."""
        e = self.engine
        e.on_state_change   = self._on_state_change
        e.on_transcript     = self._on_transcript
        e.on_suggestion     = self._on_suggestions
        e.on_confirm_needed = self._on_confirm_needed

        # Set LEDs green
        self._root.after(500, self._set_leds_ready)

        # Welcome message
        self._root.after(800, lambda: self._append_transcript(
            "system", "J.A.R.V.I.S initialized. Speak 'Hey Jarvis' or type below."
        ))

    def _set_leds_ready(self) -> None:
        self._led_mic.set_color(COLORS["orb_listen"])
        self._led_ai.set_color(COLORS["orb_speak"])
        self._led_memory.set_color(COLORS["orb_think"])

    # ─── Engine Callbacks (called from engine thread) ─────────────────────────

    def _on_state_change(self, state: str) -> None:
        self._root.after(0, self._apply_state, state)

    def _on_transcript(self, role: str, text: str) -> None:
        self._root.after(0, self._append_transcript, role, text)

    def _on_suggestions(self, suggestions: list) -> None:
        self._root.after(0, self._show_suggestions, suggestions)

    def _on_confirm_needed(self, message: str) -> bool:
        """Block until user responds in GUI."""
        result = {"value": False}
        done   = threading.Event()

        def _ask():
            from tkinter import messagebox
            result["value"] = messagebox.askyesno(
                "Jarvis — Confirmation", message,
                parent=self._root
            )
            done.set()

        self._root.after(0, _ask)
        done.wait(timeout=30)
        return result["value"]

    # ─── GUI State Application ────────────────────────────────────────────────

    def _apply_state(self, state: str) -> None:
        self._orb.set_state(state)
        is_listening = (state == "listening")
        self._waveform.set_active(is_listening)

        status_map = {
            "idle":      ("● STANDBY",    COLORS["text_secondary"]),
            "listening": ("● LISTENING",  COLORS["orb_listen"]),
            "thinking":  ("● PROCESSING", COLORS["orb_think"]),
            "speaking":  ("● SPEAKING",   COLORS["orb_speak"]),
            "error":     ("● ERROR",      COLORS["orb_error"]),
        }
        text, color = status_map.get(state, ("● STANDBY", COLORS["text_secondary"]))
        self._status_label.config(text=text, fg=color)

    def _append_transcript(self, role: str, text: str) -> None:
        self._transcript.config(state=tk.NORMAL)
        ts  = datetime.now().strftime("%H:%M")

        if role == "user":
            prefix = f"\n[{ts}]  You"
            self._transcript.insert(tk.END, f"\n{prefix}\n", ("time",))
            self._transcript.insert(tk.END, f"  {text}\n", ("user",))
        elif role == "jarvis":
            prefix = f"[{ts}]  Jarvis"
            self._transcript.insert(tk.END, f"{prefix}\n", ("time",))
            self._transcript.insert(tk.END, f"  {text}\n\n", ("jarvis",))
        else:
            self._transcript.insert(tk.END, f"\n  ─ {text} ─\n\n", ("system",))

        self._transcript.see(tk.END)
        self._transcript.config(state=tk.DISABLED)

    def _show_suggestions(self, suggestions: list) -> None:
        for chip in self._suggestion_chips:
            chip.destroy()
        self._suggestion_chips.clear()

        for sug in suggestions[:4]:
            chip = SuggestionChip(
                self._suggestion_frame, sug,
                on_click=self._on_suggestion_click
            )
            chip.pack(side=tk.LEFT, padx=4, pady=2)
            self._suggestion_chips.append(chip)

    # ─── User Interactions ────────────────────────────────────────────────────

    def _on_mic_toggle(self) -> None:
        """Manually trigger listening."""
        self._mic_active = not self._mic_active
        if self._mic_active:
            self._mic_btn.config(text="🔴  Listening...", bg=COLORS["orb_error"])
            threading.Thread(target=self._manual_listen, daemon=True).start()
        else:
            self._mic_btn.config(text="🎤  Hold to Speak", bg=COLORS["glow"])

    def _manual_listen(self) -> None:
        """Trigger one-shot listen via engine."""
        self._apply_state("listening")
        text = self.engine.listen_mode.listen_for_command()
        self._mic_active = False
        self._root.after(0, lambda: self._mic_btn.config(
            text="🎤  Hold to Speak", bg=COLORS["glow"]
        ))
        if text:
            self._root.after(0, self._append_transcript, "user", text)
            threading.Thread(
                target=self.engine.process_input, args=(text,), daemon=True
            ).start()

    def _on_send_text(self) -> None:
        text = self._input_var.get().strip()
        if text and text != "Type a command or question...":
            self._input_var.set("")
            self._append_transcript("user", text)
            threading.Thread(
                target=self.engine.process_input, args=(text,), daemon=True
            ).start()

    def _on_enter_pressed(self, event) -> None:
        self._on_send_text()

    def _on_suggestion_click(self, text: str) -> None:
        self._append_transcript("user", text)
        threading.Thread(
            target=self.engine.process_input, args=(text,), daemon=True
        ).start()

    def _on_entry_focus_in(self, event) -> None:
        if self._input_var.get() == "Type a command or question...":
            self._input_entry.delete(0, tk.END)
            self._input_entry.config(fg=COLORS["text_primary"])

    def _on_entry_focus_out(self, event) -> None:
        if not self._input_var.get():
            self._input_entry.insert(0, "Type a command or question...")
            self._input_entry.config(fg=COLORS["text_secondary"])

    def _on_close(self) -> None:
        self._orb.stop()
        self._waveform.stop()
        self.engine.shutdown()
        self._root.destroy()

    # ─── Clock ────────────────────────────────────────────────────────────────

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%a  %d %b  %I:%M:%S %p")
        self._time_label.config(text=now)
        self._root.after(1000, self._update_clock)

    # ─── Run ──────────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the Tkinter main loop (blocks until window closed)."""
        self._root.mainloop()
