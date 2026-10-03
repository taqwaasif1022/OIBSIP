# ============================================================
# APEX AI — Advanced Voice Assistant
# Oasis Infobyte Python Programming Internship — Task 1
# ============================================================

import os
import ast
import json
import re
import threading
import webbrowser
import operator
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from tavily import TavilyClient
from ddgs import DDGS

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Keep existing email configuration compatible
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "").strip()
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "").strip()

# Also support alternative names if present
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "").strip() or GMAIL_EMAIL
EMAIL_APP_PASSWORD = (
    os.getenv("EMAIL_APP_PASSWORD", "").strip()
    or GMAIL_PASSWORD
)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()


if not TAVILY_API_KEY:
    print("⚠️ Warning: TAVILY_API_KEY is not configured.")

if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY is not configured.")


# ============================================================
# FILES
# ============================================================

CUSTOM_COMMANDS_FILE = BASE_DIR / "custom_commands.json"
KNOWLEDGE_BASE_FILE = BASE_DIR / "knowledge_base.json"


# ============================================================
# SPEECH
# ============================================================

recognizer = sr.Recognizer()

# Prevent multiple TTS engines from speaking at the same time.
speech_lock = threading.Lock()


def speak(text: str):
    """
    Speak text using pyttsx3.

    A new engine is created for each speech request.
    This avoids the 'run loop already started' problem
    when reminders speak from a background thread.
    """
    if not text:
        return

    text = str(text).strip()

    print(f"\n🤖 Apex: {text}")

    with speech_lock:
        engine = None

        try:
            engine = pyttsx3.init()

            engine.setProperty("rate", 175)
            engine.setProperty("volume", 1.0)

            engine.say(text)
            engine.runAndWait()

        except Exception as exc:
            print(f"TTS Error: {exc}")

        finally:
            try:
                if engine is not None:
                    engine.stop()
            except Exception:
                pass


def listen():
    """
    Listen for a voice command using the microphone.
    """

    with sr.Microphone() as source:

        print("\n🎙️ Listening...")

        try:
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.4
            )

            audio = recognizer.listen(
                source,
                timeout=6,
                phrase_time_limit=15
            )

        except sr.WaitTimeoutError:
            print("⏱️ Listening timed out.")
            return ""

        except Exception as exc:
            print(f"Microphone Error: {exc}")
            return ""

    try:

        text = recognizer.recognize_google(audio)

        print(f"👤 You: {text}")

        return text.strip()

    except sr.UnknownValueError:

        print("❓ Sorry, I couldn't understand you.")

        return ""

    except sr.RequestError as exc:

        print(f"Speech Recognition Error: {exc}")

        return ""

    except Exception as exc:

        print(f"Speech Error: {exc}")

        return ""


# ============================================================
# CUSTOM COMMANDS
# ============================================================

DEFAULT_CUSTOM_COMMANDS = {
    "say hello": {
        "type": "say",
        "value": "Hello! Welcome to Apex AI."
    },
    "introduce yourself": {
        "type": "say",
        "value": "I am Apex, an AI-powered voice assistant."
    },
    "open apex website": {
        "type": "url",
        "value": "https://taqwaasif1022.github.io/apex-ai-agent/"
    }
}


def load_custom_commands():
    """
    Load custom commands from custom_commands.json.
    """

    if not CUSTOM_COMMANDS_FILE.exists():

        try:
            with open(
                CUSTOM_COMMANDS_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    DEFAULT_CUSTOM_COMMANDS,
                    file,
                    indent=4
                )

        except Exception as exc:
            print(f"Custom command file error: {exc}")

        return DEFAULT_CUSTOM_COMMANDS.copy()

    try:

        with open(
            CUSTOM_COMMANDS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as exc:

        print(f"Custom command load error: {exc}")

    return DEFAULT_CUSTOM_COMMANDS.copy()


def save_custom_commands(commands):
    """
    Save custom commands safely.
    """

    try:

        with open(
            CUSTOM_COMMANDS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                commands,
                file,
                indent=4
            )

        return True

    except Exception as exc:

        print(f"Custom command save error: {exc}")

        return False


@tool
def run_custom_command(command: str) -> str:
    """
    Run a user-defined command from custom_commands.json.
    """

    commands = load_custom_commands()

    requested = command.lower().strip()

    # Exact match first
    if requested in commands:

        item = commands[requested]

        action_type = str(
            item.get("type", "say")
        ).lower()

        value = str(
            item.get("value", "")
        ).strip()

        if action_type == "url":

            if value.startswith(("http://", "https://")):
                return f"OPEN_URL:{value}"

            return "The custom URL is invalid."

        return value

    # Partial match
    for name, item in commands.items():

        if name.lower() in requested:

            action_type = str(
                item.get("type", "say")
            ).lower()

            value = str(
                item.get("value", "")
            ).strip()

            if action_type == "url":

                if value.startswith(("http://", "https://")):
                    return f"OPEN_URL:{value}"

                return "The custom URL is invalid."

            return value

    return (
        f"I couldn't find a custom command named "
        f"'{command}'."
    )


@tool
def add_custom_command(
    name: str,
    action_type: str,
    value: str
) -> str:
    """
    Add a custom voice command.

    action_type can be:
    - say
    - url
    """

    name = name.strip().lower()
    action_type = action_type.strip().lower()
    value = value.strip()

    if not name:
        return "The command name cannot be empty."

    if action_type not in {"say", "url"}:
        return "Action type must be either say or url."

    if action_type == "url":
        if not value.startswith(("http://", "https://")):
            return "The URL must start with http:// or https://."

    commands = load_custom_commands()

    commands[name] = {
        "type": action_type,
        "value": value
    }

    if save_custom_commands(commands):

        return (
            f"Custom command '{name}' has been saved."
        )

    return "I couldn't save the custom command."


# ============================================================
# KNOWLEDGE BASE
# ============================================================

DEFAULT_KNOWLEDGE_BASE = {
    "apex ai": (
        "Apex AI is an AI-powered voice assistant "
        "developed as part of the Oasis Infobyte "
        "Python Programming Internship."
    ),

    "python": (
        "Python is a high-level general-purpose "
        "programming language known for its readable syntax."
    ),

    "artificial intelligence": (
        "Artificial Intelligence is the field of building "
        "systems that can perform tasks that normally "
        "require human intelligence."
    ),

    "machine learning": (
        "Machine Learning is a branch of AI where systems "
        "learn patterns from data to make predictions "
        "or decisions."
    ),

    "generative ai": (
        "Generative AI refers to AI systems that can "
        "generate content such as text, images, audio "
        "or code."
    )
}


def load_knowledge_base():

    if not KNOWLEDGE_BASE_FILE.exists():

        try:

            with open(
                KNOWLEDGE_BASE_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    DEFAULT_KNOWLEDGE_BASE,
                    file,
                    indent=4
                )

        except Exception as exc:
            print(f"Knowledge base error: {exc}")

        return DEFAULT_KNOWLEDGE_BASE.copy()

    try:

        with open(
            KNOWLEDGE_BASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as exc:

        print(f"Knowledge base load error: {exc}")

    return DEFAULT_KNOWLEDGE_BASE.copy()


@tool
def local_knowledge(question: str) -> str:
    """
    Search the local knowledge base.
    """

    question_lower = question.lower()

    knowledge = load_knowledge_base()

    for key, answer in knowledge.items():

        if key.lower() in question_lower:

            return str(answer)

    return (
        "No matching information was found "
        "in the local knowledge base."
    )


# ============================================================
# TIME
# ============================================================

@tool
def get_current_time() -> str:
    """
    Get the current system time.

    IMPORTANT:
    The existing system/laptop timezone is intentionally used.
    """

    return datetime.now().strftime("%I:%M %p")


@tool
def get_current_date() -> str:
    """
    Get the current system date.
    """

    return datetime.now().strftime(
        "%A, %B %d, %Y"
    )


# ============================================================
# CALCULATOR
# ============================================================

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.FloorDiv: operator.floordiv,
}


def safe_calculate_node(node):

    if isinstance(node, ast.Expression):
        return safe_calculate_node(node.body)

    if isinstance(node, ast.Constant):

        if isinstance(
            node.value,
            (int, float)
        ):
            return node.value

        raise ValueError("Invalid number.")

    if isinstance(node, ast.UnaryOp):

        operation = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operation is None:
            raise ValueError("Invalid operator.")

        return operation(
            safe_calculate_node(node.operand)
        )

    if isinstance(node, ast.BinOp):

        operation = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operation is None:
            raise ValueError("Invalid operator.")

        left = safe_calculate_node(node.left)
        right = safe_calculate_node(node.right)

        return operation(left, right)

    raise ValueError("Unsupported expression.")


@tool
def calculate(expression: str) -> str:
    """
    Safely calculate a mathematical expression.
    """

    try:

        expression = expression.replace(
            "^",
            "**"
        )

        tree = ast.parse(
            expression,
            mode="eval"
        )

        result = safe_calculate_node(tree)

        return str(result)

    except Exception:

        return (
            "I couldn't calculate that expression."
        )


# ============================================================
# TAVILY WEB SEARCH
# ============================================================

@tool
def web_search(query: str) -> str:
    """
    Search the web using Tavily.
    """

    if not TAVILY_API_KEY:

        return (
            "Tavily API key is not configured."
        )

    try:

        print(
            f"\n🌐 Tavily searching: {query}"
        )

        client = TavilyClient(
            api_key=TAVILY_API_KEY
        )

        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )

        items = results.get(
            "results",
            []
        )

        if not items:

            return "No useful web results were found."

        formatted = []

        for item in items:

            title = item.get(
                "title",
                "Untitled"
            )

            content = item.get(
                "content",
                ""
            )

            url = item.get(
                "url",
                ""
            )

            formatted.append(
                f"{title}\n{content}\n{url}"
            )

        return "\n\n".join(formatted)

    except Exception as exc:

        print(f"Tavily Error: {exc}")

        return (
            "Web search is temporarily unavailable."
        )


# ============================================================
# NEWS
# ============================================================

@tool
def search_news(query: str) -> str:
    """
    Search recent news.
    """

    try:

        print(
            f"\n📰 Searching news: {query}"
        )

        with DDGS() as ddgs:

            results = list(
                ddgs.news(
                    query,
                    max_results=5
                )
            )

        if not results:

            return "No news results were found."

        output = []

        for item in results:

            title = item.get(
                "title",
                "Untitled"
            )

            source = item.get(
                "source",
                ""
            )

            url = item.get(
                "url",
                ""
            )

            output.append(
                f"{title} — {source}\n{url}"
            )

        return "\n\n".join(output)

    except Exception as exc:

        print(f"News Error: {exc}")

        return (
            "News search is temporarily unavailable."
        )


# ============================================================
# LIVE WEATHER — OPEN-METEO
# ============================================================

WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail"
}


@tool
def get_weather(city: str) -> str:
    """
    Get live weather using Open-Meteo.
    No API key is required.
    """

    city = city.strip()

    if not city:

        return "Please provide a city name."

    try:

        # First find city coordinates
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=10
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        results = geo_data.get(
            "results",
            []
        )

        if not results:

            return (
                f"I couldn't find the location '{city}'."
            )

        location = results[0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        display_name = location.get(
            "name",
            city
        )

        country = location.get(
            "country",
            ""
        )

        # Get current weather
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto"
            },
            timeout=10
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        current = weather_data.get(
            "current",
            {}
        )

        temperature = current.get(
            "temperature_2m"
        )

        feels_like = current.get(
            "apparent_temperature"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        wind = current.get(
            "wind_speed_10m"
        )

        weather_code = current.get(
            "weather_code"
        )

        description = WEATHER_CODES.get(
            weather_code,
            "unknown conditions"
        )

        return (
            f"Current weather in {display_name}, {country}: "
            f"{description}. "
            f"Temperature {temperature}°C, "
            f"feels like {feels_like}°C, "
            f"humidity {humidity}%, "
            f"wind speed {wind} km/h."
        )

    except requests.RequestException as exc:

        print(f"Weather API Error: {exc}")

        return (
            "The live weather service is temporarily "
            "unavailable."
        )

    except Exception as exc:

        print(f"Weather Error: {exc}")

        return (
            "I couldn't retrieve the weather right now."
        )


# ============================================================
# OPEN WEBSITE / BROWSER SEARCH
# ============================================================

@tool
def open_website(site: str) -> str:
    """
    Open a website in the default browser.
    """

    site = site.strip()

    if not site:

        return "Please specify a website."

    common_sites = {
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "linkedin": "https://www.linkedin.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "chatgpt": "https://chatgpt.com",
        "youtube": "https://www.youtube.com"
    }

    key = site.lower()

    if key in common_sites:

        return f"OPEN_URL:{common_sites[key]}"

    if site.startswith(
        ("http://", "https://")
    ):

        return f"OPEN_URL:{site}"

    if "." in site and " " not in site:

        return f"OPEN_URL:https://{site}"

    url = (
        "https://www.google.com/search?q="
        + quote_plus(site)
    )

    return f"OPEN_URL:{url}"


@tool
def open_search_in_browser(query: str) -> str:
    """
    Open a Google search in the browser.
    """

    query = query.strip()

    if not query:

        return "Please provide a search query."

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    return f"OPEN_URL:{url}"


# ============================================================
# EMAIL
# ============================================================

@tool
def send_email(
    to: str,
    subject: str,
    body: str
) -> str:
    """
    Send an email using Gmail SMTP.
    """

    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:

        return (
            "Email is not configured. "
            "Please configure GMAIL_EMAIL and "
            "GMAIL_PASSWORD in the .env file."
        )

    to = to.strip()
    subject = subject.strip()
    body = body.strip()

    if not to or "@" not in to:

        return "Please provide a valid recipient email address."

    if not subject:

        subject = "Message from Apex AI"

    if not body:

        return "The email body cannot be empty."

    try:

        from email.message import EmailMessage
        import smtplib

        message = EmailMessage()

        message["From"] = EMAIL_ADDRESS
        message["To"] = to
        message["Subject"] = subject

        message.set_content(body)

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=20
        ) as server:

            server.login(
                EMAIL_ADDRESS,
                EMAIL_APP_PASSWORD
            )

            server.send_message(message)

        return (
            f"Email successfully sent to {to}."
        )

    except smtplib.SMTPAuthenticationError:

        return (
            "Email authentication failed. "
            "Check the Gmail address and App Password."
        )

    except Exception as exc:

        print(f"Email Error: {exc}")

        return (
            "I couldn't send the email. "
            "Please check your email settings."
        )


# ============================================================
# REMINDERS
# ============================================================

active_reminders = []
reminder_lock = threading.Lock()


def reminder_alert(message: str):
    """
    Called when a reminder timer finishes.
    """

    print(
        f"\n\n⏰ REMINDER: {message}"
    )

    # Speech happens after timer finishes.
    speak(
        f"Reminder: {message}"
    )

    with reminder_lock:

        if message in active_reminders:

            active_reminders.remove(message)


def create_reminder(seconds: float, message: str):

    timer = threading.Timer(
        seconds,
        reminder_alert,
        args=(message,)
    )

    # Important:
    # Timer must not prevent the assistant from closing.
    timer.daemon = True

    timer.start()

    with reminder_lock:

        active_reminders.append(message)

    return timer


@tool
def set_reminder(
    minutes: float,
    message: str
) -> str:
    """
    Set a reminder after a number of minutes.
    """

    try:

        minutes = float(minutes)

    except Exception:

        return "Please provide a valid number of minutes."

    message = message.strip()

    if minutes <= 0:

        return "Reminder time must be greater than zero."

    if not message:

        return "Please provide a reminder message."

    seconds = minutes * 60

    create_reminder(
        seconds,
        message
    )

    if minutes == 1:

        time_text = "1 minute"

    else:

        time_text = f"{minutes:g} minutes"

    return (
        f"Reminder set for {time_text}: {message}"
    )


@tool
def set_reminder_seconds(
    seconds: int,
    message: str
) -> str:
    """
    Set a reminder after a number of seconds.
    Useful for testing.
    """

    try:

        seconds = int(seconds)

    except Exception:

        return "Please provide a valid number of seconds."

    if seconds <= 0:

        return "Reminder time must be greater than zero."

    message = message.strip()

    if not message:

        return "Please provide a reminder message."

    create_reminder(
        seconds,
        message
    )

    return (
        f"Reminder set for {seconds} seconds: "
        f"{message}"
    )


# ============================================================
# DIRECT COMMAND HANDLING
# ============================================================

def handle_direct_command(command: str):
    """
    Handle commands that do not need Gemini.
    """

    text = command.lower().strip()

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    exit_words = {
        "exit",
        "quit",
        "goodbye",
        "bye",
        "stop",
        "shutdown"
    }

    if text in exit_words:

        return "__EXIT__"

    # --------------------------------------------------------
    # CUSTOM COMMAND
    # --------------------------------------------------------

    custom_match = re.match(
        r"^(?:run|execute)\s+custom\s+command\s+(.+)$",
        text
    )

    if custom_match:

        command_name = custom_match.group(1).strip()

        return run_custom_command.invoke(
            {
                "command": command_name
            }
        )

    # --------------------------------------------------------
    # SIMPLE REMINDER
    # --------------------------------------------------------

    reminder_match = re.match(
        r"^remind me in "
        r"(\d+(?:\.\d+)?)\s*"
        r"(second|seconds|minute|minutes|hour|hours)"
        r"\s+(?:to\s+)?(.+)$",
        text
    )

    if reminder_match:

        amount = float(
            reminder_match.group(1)
        )

        unit = reminder_match.group(2)

        message = reminder_match.group(3).strip()

        if "second" in unit:

            seconds = amount

        elif "minute" in unit:

            seconds = amount * 60

        else:

            seconds = amount * 3600

        create_reminder(
            seconds,
            message
        )

        if "hour" in unit:

            time_text = f"{amount:g} hour(s)"

        elif "minute" in unit:

            time_text = f"{amount:g} minute(s)"

        else:

            time_text = f"{amount:g} second(s)"

        return (
            f"Reminder set for {time_text}: "
            f"{message}"
        )

    # --------------------------------------------------------
    # COMMON WEBSITE COMMANDS
    # --------------------------------------------------------

    direct_sites = {
        "open google": "google",
        "open gmail": "gmail",
        "open github": "github",
        "open linkedin": "linkedin",
        "open facebook": "facebook",
        "open instagram": "instagram",
        "open chatgpt": "chatgpt",
        "open youtube": "youtube"
    }

    if text in direct_sites:

        return open_website.invoke(
            {
                "site": direct_sites[text]
            }
        )

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    search_match = re.match(
        r"^(?:search for|google)\s+(.+)$",
        text
    )

    if search_match:

        query = search_match.group(1).strip()

        return open_search_in_browser.invoke(
            {
                "query": query
            }
        )

    return None


# ============================================================
# TOOLS
# ============================================================

tools = [
    get_current_time,
    get_current_date,
    calculate,
    web_search,
    search_news,
    get_weather,
    open_website,
    open_search_in_browser,
    send_email,
    set_reminder,
    set_reminder_seconds,
    local_knowledge,
    run_custom_command,
    add_custom_command
]


# ============================================================
# GEMINI AGENT
# ============================================================

SYSTEM_PROMPT = """
You are Apex, a helpful intelligent voice assistant.

Your job is to answer naturally and perform actions using tools.

IMPORTANT TOOL RULES:

1. Use get_current_time when the user asks for the current time.

2. Use get_current_date when the user asks for today's date.

3. Use get_weather for weather requests.

4. Use send_email when the user asks to send an email.
   Ask for recipient, subject, and body if information is missing.

5. Use set_reminder for reminders expressed in minutes or hours.

6. Use set_reminder_seconds for very short testing reminders.

7. Use web_search for current information that needs web research.

8. Use search_news for news requests.

9. Use calculate for mathematical calculations.

10. Use open_website when the user asks to open a website.

11. Use open_search_in_browser when the user asks to search something
    in a browser.

12. Use run_custom_command for existing custom commands.

13. Use add_custom_command when the user explicitly asks to create
    a new custom command.

14. Use local_knowledge for information that may exist in the local
    knowledge base.

15. For normal general-knowledge questions, answer directly.

16. Never claim that an email was sent unless the send_email tool
    successfully reports that it was sent.

17. Keep responses concise and natural because responses are spoken
    aloud.

18. Never expose API keys, passwords, or private configuration.

19. Do not invent tool results.

You are Apex AI.
"""


agent = None

if GEMINI_API_KEY:

    try:

        # No temperature parameter here.
        # This avoids the Gemini sampling-parameter warning.
        model = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            google_api_key=GEMINI_API_KEY,
            max_retries=2
        )

        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT
        )

    except Exception as exc:

        print(
            f"Agent initialization error: {exc}"
        )


# ============================================================
# RESPONSE EXTRACTION
# ============================================================

def extract_text(value):
    """
    Convert LangChain response content into readable text.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):

        parts = []

        for item in value:

            if isinstance(item, str):

                parts.append(item)

            elif isinstance(item, dict):

                text = item.get("text")

                if text:
                    parts.append(str(text))

        return " ".join(parts).strip()

    if isinstance(value, dict):

        if "text" in value:
            return str(value["text"]).strip()

        if "content" in value:
            return extract_text(
                value["content"]
            )

        return str(value).strip()

    return str(value).strip()


# ============================================================
# ASK APEX
# ============================================================

def ask_apex(user_text: str) -> str:

    if not agent:

        return (
            "Gemini AI is not configured. "
            "Please check your API key."
        )

    try:

        print("\n🧠 Apex is thinking...")

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_text
                    }
                ]
            }
        )

        messages = result.get(
            "messages",
            []
        )

        if not messages:

            return (
                "I couldn't generate a response."
            )

        # Usually the final AI message is the last message.
        for message in reversed(messages):

            content = getattr(
                message,
                "content",
                None
            )

            text = extract_text(content)

            if text:

                return text

        return (
            "I couldn't generate a readable response."
        )

    except Exception as exc:

        error_text = str(exc)

        print(
            f"\nAgent Error: {error_text}"
        )

        error_lower = error_text.lower()

        if (
            "429" in error_lower
            or "resource_exhausted" in error_lower
            or "quota" in error_lower
        ):

            return (
                "Gemini's free-tier request limit "
                "was reached. Please try again shortly."
            )

        if (
            "503" in error_lower
            or "unavailable" in error_lower
        ):

            return (
                "Gemini is temporarily unavailable. "
                "Please try again shortly."
            )

        if (
            "ssl" in error_lower
            or "unexpected_eof" in error_lower
        ):

            return (
                "The connection to the AI service "
                "was interrupted. Please try again."
            )

        return (
            "Sorry, I ran into a temporary problem. "
            "Please try again."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=============================================="
    )

    print(
        "        🤖 APEX AI — VOICE ASSISTANT"
    )

    print(
        "==============================================\n"
    )

    speak(
        "Hello! I am Apex, your intelligent AI voice assistant. "
        "How can I help you?"
    )

    while True:

        user_text = listen()

        if not user_text:

            continue

        # ----------------------------------------------------
        # DIRECT COMMANDS
        # ----------------------------------------------------

        direct_result = handle_direct_command(
            user_text
        )

        if direct_result == "__EXIT__":

            speak(
                "Goodbye! Have a great day."
            )

            break

        if direct_result:

            if direct_result.startswith(
                "OPEN_URL:"
            ):

                url = direct_result[
                    len("OPEN_URL:"):
                ]

                try:

                    webbrowser.open(url)

                    speak(
                        "Opening it in your browser."
                    )

                except Exception as exc:

                    print(
                        f"Browser Error: {exc}"
                    )

                    speak(
                        "I couldn't open the browser."
                    )

            else:

                speak(direct_result)

            continue

        # ----------------------------------------------------
        # GEMINI
        # ----------------------------------------------------

        response = ask_apex(
            user_text
        )

        if not response:

            continue

        # ----------------------------------------------------
        # OPEN URL RESPONSE
        # ----------------------------------------------------

        if response.startswith(
            "OPEN_URL:"
        ):

            url = response[
                len("OPEN_URL:"):
            ]

            try:

                webbrowser.open(url)

                speak(
                    "Opening it in your browser."
                )

            except Exception as exc:

                print(
                    f"Browser Error: {exc}"
                )

                speak(
                    "I couldn't open the browser."
                )

            continue

        # ----------------------------------------------------
        # NORMAL RESPONSE
        # ----------------------------------------------------

        speak(response)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
# ============================================================
# STREAMLIT COMPATIBILITY
# ============================================================

def reset_conversation():
    """
    Reset conversational state for the web interface.

    The desktop assistant does not maintain a persistent
    conversation history, so there is nothing to clear here.
    This function exists for Streamlit compatibility.
    """
    return None

