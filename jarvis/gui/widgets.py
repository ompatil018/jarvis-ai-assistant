"""
gui/widgets.py — FINAL WORKING VERSION
"""

import random
import tkinter as tk
from typing import Callable

# ── Color Palette ─────────────────────────────────────────
COLORS = {
    "bg": "#050A14",
    "panel": "#0A1628",

    "orb_idle": "#1A3A6A",
    "orb_listen": "#00BFFF",
    "orb_think": "#7B2FBE",
    "orb_speak": "#00E5FF",
    "orb_error": "#FF3B3B",

    "accent": "#00BFFF",
    "accent2": "#7B2FBE",

    # ✅ TEXT COLORS (FIX)
    "text_primary": "#E0F0FF",
    "text_secondary": "#6A8FB5",
    "text_user": "#00D4FF",     # ✅ FIX
    "text_jarvis": "#A78BFA",   # ✅ FIX

    "glow": "#003A6A",
    "border": "#0D2442"
}

STATE_COLORS = {
    "idle": COLORS["orb_idle"],
    "listening": COLORS["orb_listen"],
    "thinking": COLORS["orb_think"],
    "speaking": COLORS["orb_speak"],
    "error": COLORS["orb_error"],
}

# =========================================================
# 🔵 Animated Orb
# =========================================================
class AnimatedOrb(tk.Canvas):

    def __init__(self, parent, size=200, **kwargs):
        kwargs.setdefault("bg", COLORS["bg"])  # safe

        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            **kwargs
        )

        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.r = size // 2 - 20

        self._angle = 0
        self._state = "idle"
        self._color = STATE_COLORS["idle"]

        self.animate()

    def set_state(self, state):
        self._state = state
        self._color = STATE_COLORS.get(state, COLORS["orb_idle"])

    def animate(self):
        self.delete("all")

        cx, cy, r = self.cx, self.cy, self.r

        self.create_oval(cx-r, cy-r, cx+r, cy+r, outline=self._color, width=2)

        self.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=self._angle,
            extent=120,
            outline=self._color,
            width=3,
            style=tk.ARC
        )

        self.create_oval(cx-5, cy-5, cx+5, cy+5, fill=self._color, outline="")

        self._angle = (self._angle + 5) % 360
        self.after(50, self.animate)


# =========================================================
# 📊 Waveform
# =========================================================
class WaveformBar(tk.Canvas):

    def __init__(self, parent, width=200, height=40, **kwargs):
        kwargs.setdefault("bg", COLORS["bg"])

        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            **kwargs
        )

        self.width = width
        self.height = height
        self.active = False
        self.animate()

    def set_active(self, active):
        self.active = active

    def animate(self):
        self.delete("all")

        bars = 20
        bar_width = self.width / bars

        for i in range(bars):
            h = random.randint(5, self.height) if self.active else 5
            x1 = i * bar_width
            x2 = x1 + bar_width - 2
            y1 = (self.height - h) / 2
            y2 = y1 + h

            self.create_rectangle(x1, y1, x2, y2, fill=COLORS["accent"], outline="")

        self.after(100, self.animate)


# =========================================================
# 🔴 LED Indicator
# =========================================================
class LEDIndicator(tk.Canvas):

    def __init__(self, parent, label="", size=12, **kwargs):
        kwargs.setdefault("bg", COLORS["panel"])

        super().__init__(
            parent,
            width=size + 60,
            height=size + 4,
            highlightthickness=0,
            **kwargs
        )

        self.size = size
        self.label = label
        self.color = COLORS["text_secondary"]
        self.draw()

    def set_color(self, color):
        self.color = color
        self.draw()

    def draw(self):
        self.delete("all")

        s = self.size

        self.create_oval(2, 2, s+2, s+2, fill=self.color, outline="")

        self.create_text(
            s+8,
            s//2 + 2,
            text=self.label,
            fill=COLORS["text_secondary"],
            font=("Consolas", 8),
            anchor="w"
        )


# =========================================================
# 💡 Suggestion Chip
# =========================================================
class SuggestionChip(tk.Frame):

    def __init__(self, parent, text: str, on_click: Callable, **kwargs):
        kwargs.setdefault("bg", COLORS["panel"])

        super().__init__(parent, **kwargs)

        btn = tk.Label(
            self,
            text=f"💡 {text}",
            bg=COLORS["glow"],
            fg=COLORS["accent"],
            font=("Segoe UI", 9),
            padx=10,
            pady=4,
            cursor="hand2"
        )

        btn.pack()

        btn.bind("<Button-1>", lambda e: on_click(text))
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["accent"], fg=COLORS["bg"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["glow"], fg=COLORS["accent"]))