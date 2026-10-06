"""emoji_map.py - converts :shortcodes: into Unicode emoji.

Unknown shortcodes (for example ":notarealemoji:") are left exactly as typed,
so the converter can never crash or lose text.
"""
import re

EMOJI = {
    # The four required by the task
    "smile": "😄", "heart": "❤️", "thumbsup": "👍", "laughing": "😂",
    # Extras
    "fire": "🔥", "rocket": "🚀", "grin": "😁", "joy": "😂", "wink": "😉",
    "blush": "😊", "sunglasses": "😎", "cry": "😢", "sob": "😭", "angry": "😠",
    "thinking": "🤔", "sleeping": "😴", "surprised": "😮", "kiss": "😘",
    "thumbsdown": "👎", "+1": "👍", "-1": "👎", "clap": "👏", "wave": "👋",
    "pray": "🙏", "ok_hand": "👌", "muscle": "💪", "raised_hands": "🙌",
    "eyes": "👀", "star": "⭐", "sparkles": "✨", "tada": "🎉", "party": "🥳",
    "100": "💯", "check": "✅", "x": "❌", "warning": "⚠️", "bulb": "💡",
    "coffee": "☕", "pizza": "🍕", "cake": "🎂", "beer": "🍺",
    "sun": "☀️", "moon": "🌙", "cloud": "☁️", "rainbow": "🌈",
    "dog": "🐶", "cat": "🐱", "snake": "🐍", "robot": "🤖", "computer": "💻",
    "bug": "🐛", "book": "📚", "music": "🎵", "trophy": "🏆", "gift": "🎁",
    "broken_heart": "💔", "blue_heart": "💙", "green_heart": "💚",
}

# A shortcode is a colon, letters/digits/_/+/-, and another colon.
_SHORTCODE_RE = re.compile(r":([A-Za-z0-9_+\-]+):")


def convert_shortcodes(text):
    """Replace known :shortcodes: with emoji; leave unknown ones untouched."""
    if not isinstance(text, str):
        return ""
    return _SHORTCODE_RE.sub(lambda m: EMOJI.get(m.group(1).lower(), m.group(0)), text)
