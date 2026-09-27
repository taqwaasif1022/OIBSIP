# Apex AI — Advanced Voice Assistant

A Python-based AI voice assistant developed for the **Oasis Infobyte Python Programming Internship — Task 1**.

## Features

- ??? Voice input using SpeechRecognition
- ?? Text-to-speech responses using pyttsx3
- ?? AI-powered conversational responses using Google Gemini
- ?? Natural-language command handling
- ?? Live web search using Tavily
- ?? News search
- ??? Live weather information using Open-Meteo
- ? Timed reminders with audible alerts
- ?? Email sending through Gmail SMTP
- ?? Safe mathematical calculations
- ?? Current time and date
- ?? Website opening and browser search
- ?? Custom commands through configuration
- ?? Local knowledge-base support
- ??? Error handling for unsuccessful speech recognition and external requests

## Technologies

- Python
- Google Gemini
- LangChain
- SpeechRecognition
- pyttsx3
- Tavily
- DuckDuckGo Search
- Open-Meteo
- SMTP / Gmail
- python-dotenv

## Project Structure

`	ext
OIBSIP/
+-- Python-Task1-VoiceAssistant/
    +-- app.py
    +-- voice_assistant.py
    +-- README.md
    +-- requirements.txt
    +-- .gitignore
pip install -r requirements.txt
python voice_assistant.py
Privacy

Apex AI processes voice input through speech-recognition services and may use external AI/search/weather services when their features are requested.

API keys and email credentials are stored locally in .env.
.env is excluded from Git using .gitignore.
Credentials are not intentionally displayed in assistant responses.
Email is sent only when the user requests the email feature.
Weather and web-search requests may be sent to their respective external services.
The assistant does not intentionally store personal conversation data in a permanent database.
Internship

Developed as part of the Oasis Infobyte Python Programming Internship — Task 1.

Developer: Taqwa Asif
