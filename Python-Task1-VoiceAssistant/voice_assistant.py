import os
import ast
import operator
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus
from tavily import TavilyClient

import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from ddgs import DDGS

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI


# ==========================================================
# APEX AI - INTELLIGENT VOICE AGENT
# Oasis Infobyte Python Programming Internship
# Task 1 - Advanced Voice Assistant
# ==========================================================


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")


MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


# ==========================================================
# SPEECH RECOGNITION
# ==========================================================

recognizer = sr.Recognizer()


def speak(text):
    """
    Convert Apex response into speech.
    """

    if not text:
        return

    text = str(text).strip()

    print(f"\n🤖 Apex: {text}")

    try:
        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            170
        )

        engine.setProperty(
            "volume",
            1.0
        )

        engine.say(text)

        engine.runAndWait()

        engine.stop()

    except Exception as error:
        print(
            "TTS Error:",
            error
        )


def listen():
    """
    Listen to the user's microphone.
    """

    try:

        with sr.Microphone() as source:

            print(
                "\n🎙️ Listening..."
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=20
            )


        command = recognizer.recognize_google(
            audio
        )

        print(
            f"👤 You: {command}"
        )

        return command.strip()


    except sr.WaitTimeoutError:

        speak(
            "I didn't hear anything."
        )

        return ""


    except sr.UnknownValueError:

        speak(
            "Sorry, I couldn't understand you."
        )

        return ""


    except sr.RequestError:

        speak(
            "The speech recognition service is unavailable."
        )

        return ""


    except Exception as error:

        print(
            "Microphone Error:",
            error
        )

        return ""


# ==========================================================
# TOOL 1 - TIME
# ==========================================================

@tool
def get_current_time() -> str:
    """
    Get the current local time.
    Use this tool whenever the user asks for the current time.
    """

    now = datetime.now()

    return now.strftime(
        "The current time is %I:%M %p."
    )


# ==========================================================
# TOOL 1B - TAVILY WEB SEARCH
# ==========================================================

@tool
def web_search(query: str) -> str:
    """
    Search the live web using Tavily.

    Use this for current, recent, latest, factual, or changing
    information, and whenever the user explicitly asks to search
    the web.
    """

    print(f"\n🌐 Tavily searching: {query}")

    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )

        results = response.get("results", [])

        if not results:
            return "No useful web results were found."

        output = []

        for result in results:
            title = result.get("title", "No title")
            content = result.get("content", "")
            url = result.get("url", "")

            output.append(
                f"Title: {title}\n"
                f"Content: {content}\n"
                f"Source: {url}"
            )

        return "\n\n".join(output)

    except Exception as error:
        print(f"Tavily Error: {error}")
        return "Tavily web search is temporarily unavailable."


# ==========================================================
# TOOL 2 - DATE
# ==========================================================

@tool
def get_current_date() -> str:
    """
    Get today's local date and day.
    Use this tool whenever the user asks for today's date or day.
    """

    now = datetime.now()

    return now.strftime(
        "Today is %A, %B %d, %Y."
    )


# ==========================================================
# TOOL 3 - CALCULATOR
# ==========================================================

ALLOWED_OPERATORS = {

    ast.Add:
        operator.add,

    ast.Sub:
        operator.sub,

    ast.Mult:
        operator.mul,

    ast.Div:
        operator.truediv,

    ast.Pow:
        operator.pow,

    ast.Mod:
        operator.mod,

    ast.USub:
        operator.neg,

    ast.UAdd:
        operator.pos,
}


def evaluate_math_node(node):

    if isinstance(
        node,
        ast.Constant
    ):

        if isinstance(
            node.value,
            (int, float)
        ):

            return node.value

        raise ValueError(
            "Invalid value"
        )


    if isinstance(
        node,
        ast.BinOp
    ):

        left = evaluate_math_node(
            node.left
        )

        right = evaluate_math_node(
            node.right
        )

        operation = ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operation is None:

            raise ValueError(
                "Unsupported operation"
            )

        return operation(
            left,
            right
        )


    if isinstance(
        node,
        ast.UnaryOp
    ):

        value = evaluate_math_node(
            node.operand
        )

        operation = ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operation is None:

            raise ValueError(
                "Unsupported operation"
            )

        return operation(
            value
        )


    raise ValueError(
        "Invalid mathematical expression"
    )


@tool
def calculate(expression: str) -> str:
    """
    Calculate a mathematical expression.

    The expression should contain numbers and normal mathematical
    operators such as +, -, *, /, %, ** and parentheses.

    Example:
    25 + 35
    800 * 0.25
    2 ** 8
    """

    try:

        tree = ast.parse(
            expression,
            mode="eval"
        )

        result = evaluate_math_node(
            tree.body
        )

        return (
            f"The result is {result}."
        )

    except ZeroDivisionError:

        return (
            "Division by zero is not allowed."
        )

    except Exception:

        return (
            "I could not calculate that expression."
        )


# ==========================================================
# TOOL 4 - WEB SEARCH
# ==========================================================

# Web search is handled by the Tavily tool above.


# ==========================================================
# TOOL 5 - NEWS SEARCH
# ==========================================================

@tool
def search_news(query: str) -> str:
    """
    Search recent news about a topic.
    Use this when the user asks for latest news, recent news,
    or current developments.
    """

    try:

        print(
            f"\n📰 Searching news: {query}"
        )

        results = DDGS().news(
            query,
            max_results=5
        )

        if not results:

            return (
                "No recent news results were found."
            )


        formatted_results = []


        for number, result in enumerate(
            results,
            start=1
        ):

            title = result.get(
                "title",
                "No title"
            )

            body = result.get(
                "body",
                ""
            )

            source = result.get(
                "source",
                ""
            )

            date = result.get(
                "date",
                ""
            )

            url = result.get(
                "url",
                ""
            )


            formatted_results.append(
                f"""
News {number}
Title: {title}
Source: {source}
Date: {date}
Summary: {body}
URL: {url}
"""
            )


        return "\n".join(
            formatted_results
        )


    except Exception as error:

        print(
            "News Search Error:",
            error
        )

        return (
            "News search is temporarily unavailable."
        )


# ==========================================================
# TOOL 6 - WEATHER SEARCH
# ==========================================================

@tool
def get_weather(city: str) -> str:
    """
    Search the web for current weather information for a city.
    Use this whenever the user asks about weather,
    temperature, rain, or forecast.
    """

    query = (
        f"current weather in {city}"
    )

    try:

        results = DDGS().text(
            query,
            max_results=4
        )

        if not results:

            return (
                f"I couldn't find weather information "
                f"for {city}."
            )


        weather_text = []


        for result in results:

            title = result.get(
                "title",
                ""
            )

            body = result.get(
                "body",
                ""
            )

            weather_text.append(
                f"{title}: {body}"
            )


        return "\n".join(
            weather_text
        )


    except Exception as error:

        print(
            "Weather Error:",
            error
        )

        return (
            "Weather search is temporarily unavailable."
        )


# ==========================================================
# TOOL 7 - OPEN WEBSITE
# ==========================================================

@tool
def open_website(website: str) -> str:
    """
    Open a website in the user's default browser.

    Use this when the user says:
    open YouTube,
    open Google,
    open GitHub,
    open Gmail,
    or open a specific website.
    """

    website = website.strip().lower()


    common_websites = {

        "youtube":
            "https://www.youtube.com",

        "google":
            "https://www.google.com",

        "github":
            "https://github.com",

        "gmail":
            "https://mail.google.com",

        "linkedin":
            "https://www.linkedin.com",

        "chatgpt":
            "https://chatgpt.com",
    }


    if website in common_websites:

        url = common_websites[
            website
        ]


    elif website.startswith(
        "http://"
    ) or website.startswith(
        "https://"
    ):

        url = website


    else:

        if "." not in website:

            url = (
                "https://www.google.com/search?q="
                + quote_plus(website)
            )

        else:

            url = (
                "https://"
                + website
            )


    try:

        return (
            f"OPEN_URL:{url}\nI opened {website}."
        )

    except Exception as error:

        print(
            "Browser Error:",
            error
        )

        return (
            f"I couldn't open {website}."
        )


# ==========================================================
# TOOL 8 - OPEN GOOGLE SEARCH
# ==========================================================

@tool
def open_search_in_browser(query: str) -> str:
    """
    Open a Google search page in the user's browser.

    Use this only if the user specifically asks to open,
    show, or display search results in the browser.
    """

    try:

        url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        return (
            f"OPEN_URL:{url}\nI opened browser search results for {query}."
        )

    except Exception as error:

        print(
            "Browser Search Error:",
            error
        )

        return (
            "I couldn't open the browser search."
        )


# ==========================================================
# TOOL 9 - YOUTUBE SEARCH
# ==========================================================

@tool
def search_youtube(query: str) -> str:
    """
    Search YouTube and open the search results in the browser.
    Use this when the user asks to find or search for a video,
    tutorial, song, or topic on YouTube.
    """

    try:

        url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        return (
            f"OPEN_URL:{url}\nI opened YouTube results for {query}."
        )

    except Exception as error:

        print(
            "YouTube Error:",
            error
        )

        return (
            "I couldn't open YouTube search."
        )


# ==========================================================
# LANGCHAIN MODEL
# ==========================================================

model = ChatGoogleGenerativeAI(

    model=MODEL_NAME,

    google_api_key=API_KEY,

    temperature=0.2,

    max_retries=2,
)


# ==========================================================
# TOOLS
# ==========================================================

tools = [

    get_current_time,

    get_current_date,

    calculate,

    web_search,

    search_news,

    get_weather,

    open_website,

    open_search_in_browser,

    search_youtube,
]


# ==========================================================
# SYSTEM PROMPT
# ==========================================================

SYSTEM_PROMPT = """
You are Apex, an intelligent personal AI voice assistant.

Your job is to understand the user's natural-language request and
complete it using the available tools whenever appropriate.

Important rules:

1. You may use multiple tools for one user request.

2. If a user asks for current, recent, latest, live, or changing
information, use a web-search or news-search tool instead of relying
only on your internal knowledge.

3. If a user asks for weather, use the weather tool.

4. If a user asks for mathematical calculations, use the calculator.

5. If a user asks for the current time or date, use the corresponding
time/date tool.

6. If a user asks you to open a website, use the website tool.

7. If the user asks you to search YouTube, use the YouTube tool.

8. If the user asks to open search results in their browser, use the
browser search tool.

9. For normal explanations, conversations, coding questions, learning,
and general knowledge, answer directly.

10. A single request can contain multiple tasks. Complete all reasonable
parts of the request one by one.

11. Never pretend that a tool succeeded if it returned an error.

12. Keep spoken answers concise and natural. Usually use 1 to 4 short
sentences unless the user requests detail.

13. Do not use markdown tables in spoken responses.

14. You are called Apex.
"""


# ==========================================================
# CREATE LANGCHAIN AGENT
# ==========================================================

agent = create_agent(

    model=model,

    tools=tools,

    system_prompt=SYSTEM_PROMPT,
)


# ==========================================================
# CONVERSATION MEMORY
# ==========================================================

conversation = []


# ==========================================================
# EXTRACT FINAL RESPONSE
# ==========================================================

def extract_text(message):

    content = getattr(
        message,
        "content",
        ""
    )


    if isinstance(
        content,
        str
    ):

        return content.strip()


    if isinstance(
        content,
        list
    ):

        pieces = []


        for block in content:

            if isinstance(
                block,
                str
            ):

                pieces.append(
                    block
                )


            elif isinstance(
                block,
                dict
            ):

                text = block.get(
                    "text"
                )

                if text:

                    pieces.append(
                        text
                    )


        return " ".join(
            pieces
        ).strip()


    return str(
        content
    ).strip()


# ==========================================================
# DIRECT COMMANDS
# ==========================================================

def handle_direct_command(command):
    """Handle simple deterministic commands without Gemini."""

    text = command.strip().lower()

    websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "linkedin": "https://www.linkedin.com",
        "chatgpt": "https://chatgpt.com",
    }

    if text in {f"open {name}" for name in websites}:
        name = text[5:].strip()
        return f"OPEN_URL:{websites[name]}\nI opened {name}."

    if text in {"open youtube", "open youtube.com"}:
        return f"OPEN_URL:{websites['youtube']}\nI opened YouTube."

    if text.startswith("search youtube for "):
        query = command[len("search youtube for "):].strip()
        if query:
            url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
            return f"OPEN_URL:{url}\nI opened YouTube results for {query}."

    if text.startswith("youtube search "):
        query = command[len("youtube search "):].strip()
        if query:
            url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
            return f"OPEN_URL:{url}\nI opened YouTube results for {query}."

    return None


# ==========================================================
# ASK THE AGENT
# ==========================================================

def ask_apex(command):

    global conversation

    direct_response = handle_direct_command(command)

    if direct_response:
        return direct_response

    conversation.append(

        {
            "role":
                "user",

            "content":
                command,
        }

    )


    try:

        print(
            "\n🧠 Apex is thinking..."
        )


        result = agent.invoke(

            {
                "messages":
                    conversation
            }

        )


        messages = result.get(
            "messages",
            []
        )


        if messages:

            conversation = messages

            final_message = messages[-1]

            answer = extract_text(
                final_message
            )


            if answer:

                return answer


        return (
            "I completed the request, "
            "but I don't have a spoken response."
        )


    except Exception as error:

        print(
            "\nAgent Error:",
            error
        )

        # Do not keep a failed user turn in memory.
        if conversation and conversation[-1].get("role") == "user":
            conversation.pop()

        error_text = str(error).lower()

        if "429" in error_text or "resource_exhausted" in error_text or "quota" in error_text:
            return "Gemini's free-tier limit was reached. Please try again later."

        if "503" in error_text or "unavailable" in error_text:
            return "Gemini is temporarily busy. Please try again in a moment."

        return (
            "Sorry, I ran into a temporary problem "
            "while processing that request."
        )


# ==========================================================
# RESET CONVERSATION
# ==========================================================

def reset_conversation():
    """Clear Apex's conversation memory."""
    global conversation
    conversation = []


# ==========================================================
# MAIN PROGRAM
# ==========================================================

def main():

    speak(
        "Hello! I am Apex, your intelligent AI assistant. "
        "What would you like me to do?"
    )


    while True:

        command = listen()


        if not command:

            continue


        lower_command = (
            command
            .lower()
            .strip()
        )


        exit_commands = [

            "exit",

            "quit",

            "goodbye",

            "bye",

            "stop assistant",

            "close assistant",
        ]


        if lower_command in exit_commands:

            speak(
                "Goodbye! Apex is shutting down."
            )

            break


        response = ask_apex(
            command
        )

        if response.startswith("OPEN_URL:"):
            lines = response.split("\n", 1)
            url = lines[0].replace("OPEN_URL:", "", 1).strip()
            message = lines[1].strip() if len(lines) > 1 else "Done."

            try:
                webbrowser.open(url)
            except Exception as error:
                print("Browser Error:", error)

            speak(message)
        else:
            speak(response)


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()