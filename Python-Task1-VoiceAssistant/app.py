import hashlib
import io
import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components
from voice_assistant import ask_apex, speak, reset_conversation

# --------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Voice Personal Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# STYLES: IMAGE STYLED HERO BANNER & DARK THEME OVERRIDES
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    *, *::before, *::after {
        box-sizing: border-box;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Deep Space Dark Background */
    .stApp {
        background: radial-gradient(circle at 80% 50%, #150628 0%, #0c0217 50%, #05010a 100%);
        background-attachment: fixed;
        color: #FFFFFF;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Container Max Width Optimization */
    .block-container {
        max-width: 1250px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 6rem !important;
    }

    /* Top Status Bar */
    .top-status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 20px;
        margin-bottom: 30px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(217, 70, 239, 0.15);
        border-radius: 30px;
        backdrop-filter: blur(12px);
    }

    .brand-title-small {
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        color: #ffffff;
    }

    .online-indicator {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: #c084fc;
        font-weight: 700;
        background: rgba(168, 85, 247, 0.1);
        padding: 6px 14px;
        border-radius: 16px;
        border: 1px solid rgba(168, 85, 247, 0.25);
    }

    .online-pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        box-shadow: 0 0 8px #22c55e;
        animation: pulseGreen 2s infinite alternate;
    }

    @keyframes pulseGreen {
        0% { opacity: 0.3; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1.2); }
    }

    /* Hero Text Left Column */
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1.15;
        color: #ffffff;
        margin-bottom: 12px;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        color: #b3a1cc;
        line-height: 1.6;
        margin-bottom: 25px;
        max-width: 480px;
    }

    /* Wave Circle Animation Right Side */
    .wave-container {
        position: relative;
        width: 280px;
        height: 280px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .wave-ring {
        position: absolute;
        border-radius: 50%;
        border: 1.5px dashed rgba(6, 182, 212, 0.4);
        animation: waveExpand 4s infinite linear;
    }

    .wave-ring:nth-child(1) { width: 140px; height: 140px; animation-delay: 0s; border-color: rgba(6, 182, 212, 0.7); }
    .wave-ring:nth-child(2) { width: 180px; height: 180px; animation-delay: 0.8s; border-color: rgba(168, 85, 247, 0.6); }
    .wave-ring:nth-child(3) { width: 220px; height: 220px; animation-delay: 1.6s; border-color: rgba(217, 70, 239, 0.5); }
    .wave-ring:nth-child(4) { width: 260px; height: 260px; animation-delay: 2.4s; border-color: rgba(236, 72, 153, 0.3); }

    @keyframes waveExpand {
        0% { transform: scale(0.9) rotate(0deg); opacity: 0.3; }
        50% { opacity: 0.9; }
        100% { transform: scale(1.1) rotate(360deg); opacity: 0.2; }
    }

    .mic-core-circle {
        position: relative;
        z-index: 5;
        width: 100px;
        height: 100px;
        background: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 40px rgba(6, 182, 212, 0.8), 0 0 80px rgba(217, 70, 239, 0.5);
    }

    .mic-core-icon {
        font-size: 2.8rem;
        color: #06b6d4;
    }

    /* Buttons Override (Pink Gradient Read More Style) */
    .stButton > button {
        border-radius: 30px !important;
        border: none !important;
        background: linear-gradient(135deg, #a855f7 0%, #d946ef 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 20px rgba(217, 70, 239, 0.4) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(217, 70, 239, 0.7) !important;
        color: #ffffff !important;
    }

    /* Audio Mic Input Override */
    [data-testid="stAudioInput"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
    }

    [data-testid="stAudioInput"] > div {
        background: rgba(22, 6, 42, 0.8) !important;
        border: 1px solid rgba(217, 70, 239, 0.4) !important;
        border-radius: 50px !important;
        padding: 6px 16px !important;
        box-shadow: 0 0 20px rgba(217, 70, 239, 0.25) !important;
    }

    [data-testid="stAudioInput"] button {
        background: linear-gradient(135deg, #06b6d4 0%, #d946ef 100%) !important;
        color: white !important;
        border-radius: 50% !important;
        border: none !important;
        box-shadow: 0 0 12px rgba(6, 182, 212, 0.6) !important;
    }

    /* Strict Dark Bottom Input Override */
    [data-testid="stChatInput"] {
        background-color: #120324 !important;
        background: #120324 !important;
        border: 2px solid #d946ef !important;
        border-radius: 28px !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.8), 0 0 18px rgba(217, 70, 239, 0.4) !important;
    }

    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div {
        background-color: #120324 !important;
        background: #120324 !important;
        border: none !important;
        color: #ffffff !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #c084fc !important;
        -webkit-text-fill-color: #c084fc !important;
        opacity: 1 !important;
    }

    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #a855f7 0%, #d946ef 100%) !important;
        border: none !important;
        border-radius: 50% !important;
    }

    /* Chat Messages Glass Styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(217, 70, 239, 0.15) !important;
        border-radius: 18px !important;
        color: #f3f4f6 !important;
        margin-bottom: 10px !important;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SESSION STATE MANAGEMENT
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "auto_speak_responses" not in st.session_state:
    st.session_state.auto_speak_responses = True


# --------------------------------------------------
# CORE LOGIC FUNCTIONS
# --------------------------------------------------
def process_audio(audio_bytes: bytes) -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data)


def browser_speak(text: str):
    """Speak on the visitor's device/browser instead of the Streamlit server."""
    if not text:
        return
    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("</", "<\\/")
        .replace("\r", " ")
        .replace("\n", " ")
    )
    components.html(
        f"""
        <script>
        (function() {{
            const text = `{safe_text}`;
            try {{
                if ("speechSynthesis" in window) {{
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 1.0;
                    utterance.pitch = 1.0;
                    window.speechSynthesis.speak(utterance);
                }}
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        scrolling=False,
    )


def run_assistant(query: str):
    query = query.strip()
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query})

    try:
        response = ask_apex(query)
    except Exception as err:
        response = f"Error processing query: {err}"

    # Browser commands are returned as OPEN_URL:<url>.
    # The URL is handled client-side, because webbrowser.open() on the
    # Streamlit server cannot open a tab on the visitor's device.
    if isinstance(response, str) and response.startswith("OPEN_URL:"):
        lines = response.splitlines()
        url = lines[0].replace("OPEN_URL:", "", 1).strip()
        message = "\n".join(lines[1:]).strip() or "Opening it for you..."
        st.session_state.messages.append({"role": "assistant", "content": message})
        st.session_state.pending_url = url
    else:
        st.session_state.messages.append({"role": "assistant", "content": response})
        if st.session_state.auto_speak_responses:
            browser_speak(response)


# --------------------------------------------------
# BROWSER ACTION HANDLER
# --------------------------------------------------
if "pending_url" not in st.session_state:
    st.session_state.pending_url = None

if st.session_state.pending_url:
    safe_url = (
        st.session_state.pending_url
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    # Try to open automatically in the visitor's browser.
    # If the browser blocks the popup, the visible link below remains usable.
    components.html(
        f"""
        <script>
        (function() {{
            const url = "{safe_url}";
            try {{
                const opened = window.open(url, "_blank", "noopener,noreferrer");
                if (!opened) {{
                    const link = document.createElement("a");
                    link.href = url;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.textContent = "Open YouTube";
                    link.style.cssText =
                        "display:inline-block;padding:10px 16px;border-radius:22px;" +
                        "background:linear-gradient(135deg,#a855f7,#d946ef);" +
                        "color:white;text-decoration:none;font-weight:700;";
                    document.body.appendChild(link);
                }}
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=45,
        scrolling=False,
    )

    st.session_state.pending_url = None


# --------------------------------------------------
# APP LAYOUT (IMAGE-STYLED HERO SECTION)
# --------------------------------------------------

# Top Navigation Bar
st.markdown(
    """
    <div class="top-status-bar">
        <div class="brand-title-small">🎙️ VOICELY AI</div>
        <div class="online-indicator">
            <span class="online-pulse-dot"></span>
            Agent Active
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Hero Split Layout (Left Text, Right Visualizer)
col_left, col_right = st.columns([1.1, 1], gap="large")

# LEFT SIDE: Image Banner Heading & Quick Action Buttons
with col_left:
    st.markdown(
        """
        <div class="hero-title">Voice Personal<br>Assistant</div>
        <div class="hero-subtitle">
            Smart, adaptive voice assistant designed for seamless hands-free navigation and real-time intelligent conversations.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # APEX AI COMMAND CENTER
    # --------------------------------------------------

    st.markdown(
        """
        <style>
        .command-center {
            margin: 18px 0 12px;
            padding: 18px 20px;
            border: 1px solid rgba(255,255,255,.10);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(124,58,237,.13), rgba(236,72,153,.07));
            box-shadow: 0 14px 45px rgba(0,0,0,.18);
        }
        .command-kicker {
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2px;
            opacity: .55;
            margin-bottom: 6px;
        }
        .command-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
        }
        .command-title {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -.4px;
        }
        .command-subtitle {
            margin-top: 4px;
            font-size: 12px;
            opacity: .58;
        }
        .command-orb {
            width: 46px;
            height: 46px;
            min-width: 46px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            background: linear-gradient(135deg, rgba(168,85,247,.28), rgba(236,72,153,.22));
            border: 1px solid rgba(255,255,255,.12);
            box-shadow: 0 0 28px rgba(168,85,247,.20);
        }
        .command-label {
            font-size: 11px;
            font-weight: 700;
            opacity: .65;
            margin: 12px 0 8px;
        }
        </style>

        <div class="command-center">
            <div class="command-kicker">APEX AI &bull; COMMAND CENTER</div>
            <div class="command-heading">
                <div>
                    <div class="command-title">What do you want to build?</div>
                    <div class="command-subtitle">Pick a mode or talk to Apex with your voice.</div>
                </div>
                <div class="command-orb">&#10022;</div>
            </div>
        </div>
        <div class="command-label">EXPLORE APEX MODES</div>
        """,
        unsafe_allow_html=True,
    )

    command_cols = st.columns(4)

    commands = [
        ("🧠", "Ask Anything", "Explain, solve & learn",
         "Explain machine learning in simple words."),
        ("🔎", "Research Mode", "Find & summarize",
         "Research the latest trends in AI agents."),
        ("💡", "Idea Lab", "Create new ideas",
         "Give me 5 unique AI project ideas."),
        ("⚙️", "Build With AI", "Code & create",
         "Help me build an AI chatbot with Python."),
    ]

    for col, (icon, title, subtitle, query) in zip(command_cols, commands):
        with col:
            if st.button(
                f"{icon}  {title}\n{subtitle}",
                key=f"command_{title.lower().replace(' ', '_')}",
                use_container_width=True,
            ):
                run_assistant(query)
                st.rerun()

    st.write("")
    # Clickable Mic Input
    recorded_audio = st.audio_input("Record audio", label_visibility="collapsed")

    if recorded_audio is not None:
        audio_bytes = recorded_audio.getvalue()
        current_hash = hashlib.sha256(audio_bytes).hexdigest()

        if current_hash != st.session_state.last_audio_hash:
            st.session_state.last_audio_hash = current_hash
            with st.spinner("Processing voice..."):
                try:
                    text = process_audio(audio_bytes)
                    st.toast(f'🎙️ You said: "{text}"')
                    run_assistant(text)
                    st.rerun()
                except Exception:
                    st.warning("Could not understand audio.")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.session_state.auto_speak_responses = st.toggle(
            "🔊 Auto Read Aloud", value=st.session_state.auto_speak_responses
        )
    with c2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_audio_hash = None
            try:
                reset_conversation()
            except Exception:
                pass
            st.rerun()

# RIGHT SIDE: Image Wave Ring Visualizer & Chat Window
with col_right:
    # Wave Mic Circle Animation (Matching the reference image)
    st.markdown(
        """
        <div class="wave-container">
            <div class="wave-ring"></div>
            <div class="wave-ring"></div>
            <div class="wave-ring"></div>
            <div class="wave-ring"></div>
            <div class="mic-core-circle">
                <span class="mic-core-icon">🎙️</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💬 Live Conversation")

    chat_box = st.container(height=320)
    with chat_box:
        if not st.session_state.messages:
            st.info("👋 Tap the mic or click a button above to start chatting.")

        for idx, msg in enumerate(st.session_state.messages):
            avatar = "👤" if msg["role"] == "user" else "🎙️"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])
                if msg["role"] == "assistant":
                    if st.button("🔊 Read", key=f"speak_{idx}"):
                        browser_speak(msg["content"])

# Fixed Dark Bottom Chat Input
prompt = st.chat_input("Type a message or command...")
if prompt:
    run_assistant(prompt)
    st.rerun()
