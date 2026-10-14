# 🎙️ Voicely AI — Advanced Voice Assistant

**An AI-powered voice assistant | Oasis Infobyte Python Programming Internship — Task 1**

A modern, fully-featured voice assistant built with **Python**, **Streamlit**, **LangChain**, and **Groq (Llama / GPT-OSS)**. Voicely AI listens to voice commands, responds with natural speech, performs real-world tasks (web search, weather, news, email, reminders), and controls your PC — hands-free.

---

## 🌐 Live Web Demo

A browser-based version of Voicely AI is available through **Streamlit Cloud**.

**Live Demo:** [voicely-ai.streamlit.app](https://voicely-ai.streamlit.app/)

The web demo provides:

- 🎤 Voice input via browser microphone
- 🔊 Auto speech playback (Web Speech API)
- 💬 Live conversation window
- 🧠 AI-powered responses (Groq — Llama 3 / GPT-OSS)
- 🌦️ Live weather, news, and web search
- 📧 Email sending via Gmail SMTP
- ⏰ Timed reminders
- 🎨 Modern dark UI with animated visuals
- 📱 Fully responsive interface

> **Note:** The official internship implementation is the **Python desktop application**. The Streamlit version is a browser-based port of the same backend (`voice_assistant.py`).

---

## ✨ Project Preview

Voicely AI provides a clean, modern interface designed to make hands-free voice interaction simple and intuitive.

---

## 🚀 Main Features

- 🧠 **AI-powered conversations** — Google Gemini / Groq (Llama 3.3 70B, GPT-OSS 120B)
- 🎤 **Voice input** — SpeechRecognition + Google Speech API
- 🔊 **Text-to-speech responses** — pyttsx3 (desktop) + Web Speech API (browser)
- 🌐 **Live web search** — Tavily API
- 📰 **Live news search** — DuckDuckGo Search
- 🌦️ **Live weather** — Open-Meteo (no API key required)
- 🧮 **Safe math calculations** — AST-based evaluator
- ⏰ **Timed reminders** with audible alerts
- 📧 **Email sending** — Gmail SMTP with App Password
- 🌍 **Website opener** — Google, YouTube, GitHub, LinkedIn, Gmail, etc.
- 🔗 **Browser search** — Google search from voice
- 📚 **Local knowledge base** — Offline Q&A support
- 🎯 **Custom commands** — User-defined say/URL commands
- 💻 **PC control** — Shutdown, restart, sleep, lock (Windows only)
- 🛡️ **Error handling** — Graceful fallbacks for API/speech failures

---

## 🎯 Voice Command Categories

| Category | Example Command | Action |
|---|---|---|
| 🕐 Time & Date | *"What time is it?"* | Speaks current system time |
| 🌦️ Weather | *"Weather in Karachi"* | Live weather via Open-Meteo |
| 📰 News | *"Latest news about AI"* | Fetches recent headlines |
| 🔍 Web Search | *"Search for Python tutorials"* | Tavily web search |
| 🧮 Math | *"Calculate 25 times 4"* | Safe AST calculation |
| 📧 Email | *"Send email to x@y.com"* | Gmail SMTP |
| ⏰ Reminders | *"Remind me in 5 minutes to study"* | Timed reminder |
| 🌐 Open Sites | *"Open YouTube"* | Opens in browser |
| 💻 PC Control | *"Shutdown my PC"* | Windows shutdown (with confirmation) |
| 📚 Knowledge | *"What is machine learning?"* | Local knowledge base |

---

## 🧮 Technologies

### Desktop Application

| Technology | Purpose |
|---|---|
| **Python 3.13** | Core application language |
| **SpeechRecognition** | Voice input via microphone |
| **pyttsx3** | Offline text-to-speech engine |
| **LangChain** | Agent + tool orchestration framework |
| **Groq API** | Ultra-fast LLM inference (Llama 3.3 70B, GPT-OSS 120B) |
| **Tavily** | Advanced web search |
| **DuckDuckGo Search** | Live news |
| **Open-Meteo** | Free weather API (no key) |
| **SMTP (Gmail)** | Email sending |
| **python-dotenv** | Environment variable management |
| **ZoneInfo** | Timezone handling |

### Web Application (Streamlit)

| Technology | Purpose |
|---|---|
| **Streamlit** | Web app framework |
| **Web Speech API** | Browser-based text-to-speech |
| **HTML/CSS/JS** | Custom UI, animations, wave visualizer |
| **Streamlit Cloud** | Free deployment |

---

## 📁 Project Structure

```
OIBSIP/
├── Python-Task1-VoiceAssistant/
│   ├── app.py                    # Streamlit web app
│   ├── voice_assistant.py        # Core AI + tools + desktop app
│   ├── custom_commands.json      # User-defined commands
│   ├── knowledge_base.json       # Offline Q&A database
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # API keys (not committed)
│   ├── .gitignore
│   └── README.md
│
├── Python-Task2-BMICalculator/
├── Python-Task3-PasswordGenerator/
└── docs/
```

### File Descriptions

| File | Purpose |
|---|---|
| **`app.py`** | Streamlit web interface — chat window, mic input, voice controls |
| **`voice_assistant.py`** | Desktop assistant — speech, tools, Groq agent, PC control |
| **`custom_commands.json`** | User-defined commands (say / URL) |
| **`knowledge_base.json`** | Offline FAQ answers |
| **`requirements.txt`** | Python packages |
| **`.env`** | API keys, email credentials (excluded from Git) |

---

## ▶️ Running the Desktop Application

This project includes an official Python desktop GUI application.

```bash
python voice_assistant.py
```

The assistant will:

1. Greet you with a voice message
2. Listen through your microphone
3. Respond via speaker
4. Execute commands in real time

Say **"exit"** or **"goodbye"** to stop.

---

## 🌐 Running the Web Demo Locally

```bash
streamlit run app.py
```

Then open:

```
http://localhost:8501
```

---

## 🔑 Environment Setup

Create a `.env` file inside `Python-Task1-VoiceAssistant/`:

```env
# Required
GROQ_API_KEY=gsk_your_groq_api_key
TAVILY_API_KEY=tvly-your_tavily_key

# Optional (for email feature)
GMAIL_EMAIL=your_email@gmail.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

### Getting the API Keys

| Key | Free? | Get it from |
|---|---|---|
| **Groq API Key** | ✅ Yes | [console.groq.com](https://console.groq.com) |
| **Tavily API Key** | ✅ Free tier | [tavily.com](https://tavily.com) |
| **Gmail App Password** | ✅ Free | Google Account → Security → App Passwords |

> ⚠️ **Gmail App Password** is a 16-character code — not your regular Gmail password. Regular passwords will **not** work.

---

## 📦 Installation

```bash
cd Python-Task1-VoiceAssistant
pip install -r requirements.txt
```

### `requirements.txt`

```
streamlit
SpeechRecognition
pyttsx3
python-dotenv
tavily-python
ddgs
langchain
langchain-core
langchain-openai
openai
requests
```

---

## 🧪 Tested Functionality

### Desktop Application
- ✅ Voice input via microphone
- ✅ Text-to-speech output
- ✅ Current time & date
- ✅ Live weather (multi-city)
- ✅ Latest news
- ✅ Web search (Tavily)
- ✅ Mathematical calculations
- ✅ Email sending via Gmail
- ✅ Timed reminders (seconds / minutes / hours)
- ✅ Opening websites (Google, YouTube, GitHub, etc.)
- ✅ Browser search
- ✅ Custom commands
- ✅ Local knowledge base
- ✅ PC control — shutdown, restart, sleep, lock (Windows)
- ✅ Graceful error handling (speech, API, network)

### Web Demo
- ✅ Voice input via browser mic
- ✅ Browser-side speech synthesis
- ✅ Live chat window
- ✅ Command buttons (Ask Anything, Research, Idea Lab, Build)
- ✅ Auto Read Aloud toggle
- ✅ Stop Speaking button
- ✅ Clear Chat button
- ✅ Open URL handling
- ✅ Cloud secret loading (Streamlit)
- ✅ Responsive dark theme UI

---


## 🔐 Privacy

Voicely AI:

- Processes voice input through **speech-recognition services**
- Uses **external AI / search / weather services** only when those features are requested
- Stores API keys and email credentials locally in `.env` (excluded from Git)
- Does **not** intentionally store personal conversation data in a permanent database
- Sends email **only** when the user explicitly requests the email feature
- Never displays API keys, passwords, or private configuration in responses

---

## 📌 Internship Task

| Field | Value |
|---|---|
| **Organization** | Oasis Infobyte |
| **Program** | Python Programming Internship |
| **Task** | Task 1 — Advanced Voice Assistant |
| **Level** | Advanced |
| **Track** | Python Programming |

---

## 👩‍💻 Author

**Taqwa Asif**

AI Agents • Chatbots • Generative AI • Machine Learning • Frontend Development

- GitHub: [@taqwaasif1022](https://github.com/taqwaasif1022)
- Email: taqwaasif76@gmail.com
- Live Demo: [voicely-ai.streamlit.app](https://voicely-ai.streamlit.app/)

---

## ⚠️ Disclaimer

This project is an educational voice assistant created for the **Oasis Infobyte Python Programming Internship**.

- It performs real actions (shutdown, email, file access) — use responsibly.
- Weather, news, and AI responses are provided by third-party APIs and may occasionally be inaccurate.
- PC control features are **Windows-only** and require user confirmation.
- This is not a production-grade security product.

---

## 📄 License

This project is licensed for **educational purposes** as part of the Oasis Infobyte Internship Program.

---

⭐ **If you found this project useful, consider giving it a star!**
