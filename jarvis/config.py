"""
config.py — Central configuration for Jarvis AI Assistant.
All settings, paths, and mappings are defined here.
"""

import os
import getpass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Base Paths ───────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
LOGS_DIR  = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

USERNAME = getpass.getuser()

# ─── API Keys ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
PICOVOICE_API_KEY = os.getenv("PICOVOICE_API_KEY", "")
SERPAPI_KEY       = os.getenv("SERPAPI_KEY", "")
OPENWEATHER_KEY   = os.getenv("OPENWEATHER_KEY", "")

# ─── LLM Config ───────────────────────────────────────────────────────────────
LLM_PROVIDER    = os.getenv("LLM_PROVIDER", "openai")   # openai | groq | ollama
LLM_MODEL       = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = 0.75
LLM_MAX_TOKENS  = 600

# ─── Voice Config ─────────────────────────────────────────────────────────────
WAKE_WORDS        = ["hey jarvis", "jarvis", "hey जार्विस", "जार्विस"]
SUPPORTED_LANGS   = ["hi-IN", "en-IN", "en-US"]
STT_MODEL_SIZE    = os.getenv("WHISPER_MODEL", "base")   # tiny|base|small|medium
AUDIO_SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 300          # RMS energy threshold
SILENCE_DURATION  = 1.8          # seconds of silence to stop recording
MAX_RECORD_SECS   = 30           # max recording length

# ─── TTS Config ───────────────────────────────────────────────────────────────
TTS_ENGINE  = os.getenv("TTS_ENGINE", "pyttsx3")   # pyttsx3 | gtts
TTS_RATE    = 175
TTS_VOLUME  = 0.9

# ─── Paths ────────────────────────────────────────────────────────────────────
MEMORY_FILE       = DATA_DIR / "conversation_memory.json"
USER_PROFILE_FILE = BASE_DIR / "ai_brain" / "user_profile.json"
TASKS_FILE        = DATA_DIR / "tasks.json"
LOG_FILE          = LOGS_DIR / "jarvis.log"
PLUGINS_DIR       = BASE_DIR / "plugins"

# ─── Memory Config ────────────────────────────────────────────────────────────
MAX_MEMORY_TURNS   = 30
MAX_CONTEXT_TOKENS = 3000
MEMORY_SUMMARY_EVERY = 20   # summarize after N turns

# ─── Personality Config ───────────────────────────────────────────────────────
JARVIS_NAME        = "Jarvis"
USER_PREFERRED_NAME = os.getenv("USER_NAME", USERNAME)
ASSISTANT_LANGUAGE  = os.getenv("ASSISTANT_LANGUAGE", "auto")  # auto|en|hi

# ─── App Mappings ─────────────────────────────────────────────────────────────
APP_MAPPINGS = {
    "chrome":             rf"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome":      rf"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":            rf"C:\Program Files\Mozilla Firefox\firefox.exe",
    "vscode":             rf"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code":            rf"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": rf"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "notepad":            "notepad.exe",
    "calculator":         "calc.exe",
    "paint":              "mspaint.exe",
    "task manager":       "taskmgr.exe",
    "file explorer":      "explorer.exe",
    "cmd":                "cmd.exe",
    "command prompt":     "cmd.exe",
    "powershell":         "powershell.exe",
    "word":               rf"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":              rf"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":         rf"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "spotify":            rf"C:\Users\{USERNAME}\AppData\Roaming\Spotify\Spotify.exe",
    "vlc":                rf"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "discord":            rf"C:\Users\{USERNAME}\AppData\Local\Discord\Update.exe",
    "whatsapp":           rf"C:\Users\{USERNAME}\AppData\Local\WhatsApp\WhatsApp.exe",
    "telegram":           rf"C:\Users\{USERNAME}\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "zoom":               rf"C:\Users\{USERNAME}\AppData\Roaming\Zoom\bin\Zoom.exe",
    "settings":           "ms-settings:",
    "control panel":      "control.exe",
    "snipping tool":      "SnippingTool.exe",
    "clock":              "ms-clock:",
    "photos":             "ms-photos:",
    "edge":               rf"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge":     rf"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}

# ─── Website Mappings ─────────────────────────────────────────────────────────
WEBSITE_MAPPINGS = {
    "youtube":       "https://www.youtube.com",
    "google":        "https://www.google.com",
    "github":        "https://www.github.com",
    "gmail":         "https://mail.google.com",
    "chatgpt":       "https://chat.openai.com",
    "netflix":       "https://www.netflix.com",
    "amazon":        "https://www.amazon.in",
    "flipkart":      "https://www.flipkart.com",
    "linkedin":      "https://www.linkedin.com",
    "twitter":       "https://www.twitter.com",
    "x":             "https://www.x.com",
    "instagram":     "https://www.instagram.com",
    "facebook":      "https://www.facebook.com",
    "stackoverflow": "https://stackoverflow.com",
    "wikipedia":     "https://www.wikipedia.org",
    "reddit":        "https://www.reddit.com",
    "whatsapp web":  "https://web.whatsapp.com",
    "maps":          "https://maps.google.com",
    "translate":     "https://translate.google.com",
    "news":          "https://news.google.com",
    "drive":         "https://drive.google.com",
    "docs":          "https://docs.google.com",
    "sheets":        "https://sheets.google.com",
    "meet":          "https://meet.google.com",
    "hotstar":       "https://www.hotstar.com",
    "prime":         "https://www.primevideo.com",
    "jio cinema":    "https://www.jiocinema.com",
    "spotify web":   "https://open.spotify.com",
}

# ─── Security ─────────────────────────────────────────────────────────────────
DANGEROUS_COMMANDS = [
    "format c:", "del /f /s /q", "rm -rf", "shutdown /s /f",
    "reg delete hklm", "taskkill /f /im", "cipher /w",
    ":(){:|:&};:", "deltree", "rd /s /q c:",
]
CONFIRMATION_REQUIRED_KEYWORDS = [
    "delete", "remove", "shutdown", "restart", "format",
    "uninstall", "kill", "terminate", "wipe",
    "हटाओ", "बंद करो", "डिलीट",
]

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL  = "DEBUG"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
