# J.A.R.V.I.S — AI Desktop Assistant

> **Just A Rather Very Intelligent System** — A production-level bilingual AI assistant for Windows, inspired by Iron Man's JARVIS.

---

## Features

| Category | Capabilities |
|---|---|
| 🎤 **Voice** | Wake word ("Hey Jarvis"), Hindi + English STT via Whisper, Natural TTS |
| 🧠 **AI Brain** | GPT-4o-mini / Groq / Ollama, context-aware, persistent memory |
| 🤖 **Personality** | Friend-like, bilingual, witty Jarvis persona |
| 💡 **Suggestions** | Proactive time/usage-aware suggestions |
| 🔁 **Multi-step** | "Open Chrome and go to YouTube then search Python" |
| 🌐 **Web** | DuckDuckGo search, Wikipedia, weather, news |
| 🖥️ **System** | Open apps, websites, files, volume, screenshot |
| 🔒 **Security** | Blocked/confirm/safe command tiers, GUI confirmation dialogs |
| 🔌 **Plugins** | Drop-in plugin system — create your own skills |
| 🎨 **GUI** | Futuristic dark Tkinter UI with animated orb |

---

## Quick Start

### 1. Setup

```bat
cd "d:\ai project\jarvis"
setup.bat
```

This will create a virtual environment, install all dependencies, and copy `.env.example` → `.env`.

### 2. Configure API Key

Open `.env` and set at least one:

```env
# Option A: OpenAI (paid, most capable)
OPENAI_API_KEY=sk-...

# Option B: Groq (free tier, very fast)
GROQ_API_KEY=gsk_...

# Option C: Ollama (fully local, no key needed)
# LLM_PROVIDER=ollama
```

### 3. Run

```bat
.venv\Scripts\activate
python main.py
```

---

## Manual Installation (without setup.bat)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
:: Edit .env with your key
python main.py
```

---

## Voice Commands (Examples)

| Command | Action |
|---|---|
| "Hey Jarvis" | Activate assistant |
| "Open Chrome" | Launch Chrome |
| "Open YouTube" | Navigate to YouTube |
| "Search Python tutorials on YouTube" | YouTube search |
| "What's the weather in Mumbai?" | Weather report |
| "Tell me about black holes" | Wikipedia summary |
| "Volume up / down / mute" | System volume |
| "Take a screenshot" | Captures screen |
| "Delete test.txt" | Delete with confirmation |
| "Open Chrome and then go to GitHub" | Multi-step task |
| "यूट्यूब खोलो" | Open YouTube (Hindi) |
| "मौसम बताओ" | Weather in Hindi |
| "Jarvis goodbye" | Shutdown assistant |

---

## Folder Structure

```
jarvis/
├── main.py                     # Entry point
├── config.py                   # All settings & mappings
├── .env                        # Your API keys (never commit!)
├── requirements.txt
├── setup.bat                   # Windows setup script
│
├── core/
│   ├── engine.py               # Main orchestrator
│   └── task_engine.py          # Multi-step command runner
│
├── voice_module/
│   ├── speech_recognizer.py    # Whisper / Google STT
│   ├── text_to_speech.py       # pyttsx3 / gTTS
│   ├── wake_word.py            # Wake-word detection
│   └── listening_mode.py       # Continuous listening + interrupt
│
├── ai_brain/
│   ├── llm_client.py           # OpenAI / Groq / Ollama wrapper
│   ├── intent_detector.py      # LLM + regex intent classification
│   ├── conversation_memory.py  # Persistent JSON memory
│   ├── response_generator.py   # Prompt builder
│   ├── personality_engine.py   # Jarvis persona & bilingual responses
│   ├── suggestion_engine.py    # Smart proactive suggestions
│   ├── context_engine.py       # Context awareness (time/apps/state)
│   ├── web_assistant.py        # Search / Wikipedia / Weather / News
│   └── user_profile.json       # User preferences & history
│
├── command_executor/
│   ├── app_launcher.py         # Launch desktop apps
│   ├── browser_controller.py   # Open URLs / search
│   ├── file_manager.py         # File operations
│   └── system_controller.py   # Volume / screenshot / power
│
├── security_layer/
│   ├── command_validator.py    # Blocked / confirm / safe tiers
│   └── permission_manager.py  # GUI + voice confirmation
│
├── plugins/
│   ├── plugin_manager.py       # Auto-discover & load plugins
│   └── sample_plugin/
│       └── plugin.py           # Template — copy to create your own
│
├── gui/
│   ├── main_window.py          # Futuristic Tkinter window
│   └── widgets.py              # AnimatedOrb, WaveformBar, etc.
│
├── data/                       # Auto-created
│   └── conversation_memory.json
└── logs/
    └── jarvis.log
```

---

## Creating a Plugin

1. Create `plugins/my_plugin/` folder
2. Create `plugin.py`:

```python
PLUGIN_NAME    = "MyPlugin"
PLUGIN_INTENTS = ["my_custom_intent"]

def handle(intent, entities, raw_text):
    if intent == "my_custom_intent":
        return "Hello from my plugin!"
    return None
```

3. Restart Jarvis — it will auto-discover your plugin.

---

## Configuration Reference

| Key | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` / `groq` / `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `WHISPER_MODEL` | `base` | `tiny` / `base` / `small` / `medium` |
| `TTS_ENGINE` | `pyttsx3` | `pyttsx3` (offline) / `gtts` (online) |
| `USER_NAME` | `Sir` | How Jarvis addresses you |
| `OPENWEATHER_KEY` | — | Optional, for weather feature |
| `PICOVOICE_API_KEY` | — | Optional, for precise wake-word |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `PyAudio install fails` | Install via: `pip install pipwin && pipwin install pyaudio` |
| `No TTS voice` | Install Windows Hindi voice: Settings → Time & Language → Speech |
| `Whisper slow on first run` | Model downloads once (~150 MB for base) |
| `Wake word not detecting` | Adjust `SILENCE_THRESHOLD` in config.py (default 300) |
| `LLM not responding` | Check your API key in `.env` |

---

## License

MIT — Free to use, modify, and distribute.
