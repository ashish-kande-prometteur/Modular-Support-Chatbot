import re

GREETING_PATTERNS = [
    r"^hi$",
    r"^hello$",
    r"^hey$",
    r"^hii+$",
    r"^heyy+$",
    r"^good morning$",
    r"^good afternoon$",
    r"^good evening$",
    r"^good night$",
    r"^hola$",
]

GREETING_RESPONSE = (
    "👋 Hello! Welcome to FTimer Support.\n\n"
    "I'm here to help you with:\n"
    "• Account & Login\n"
    "• Deposits & Withdrawals\n"
    "• Bonuses & Promotions\n"
    "• Betting Rules\n"
    "• Responsible Gaming\n\n"
    "How may I assist you today?"
)

# ----------------------------------------------------------
# Casual / small-talk patterns that should NOT enter the
# RAG or ticket pipeline.
# ----------------------------------------------------------
THANKS_PATTERNS = [
    r"^thanks?$",
    r"^thank\s*you$",
    r"^thanku$",
    r"^thankx$",
    r"^thx$",
    r"^ty$",
    r"^okay\s*thanks?$",
    r"^ok\s*thanks?$",
    r"^ok\s*thank\s*you$",
    r"^great\s*thanks?$",
    r"^thanks?\s*a\s*lot$",
    r"^much\s*appreciated$",
]

BYE_PATTERNS = [
    r"^bye$",
    r"^goodbye$",
    r"^good\s*bye$",
    r"^see\s*you$",
    r"^see\s*ya$",
    r"^take\s*care$",
    r"^cya$",
    r"^bye\s*bye$",
]

ACKNOWLEDGEMENT_PATTERNS = [
    r"^ok$",
    r"^okay$",
    r"^okk+$",
    r"^okaay+$",
    r"^got\s*it$",
    r"^understood$",
    r"^alright$",
    r"^sure$",
    r"^fine$",
    r"^cool$",
    r"^nice$",
    r"^great$",
    r"^perfect$",
    r"^awesome$",
    r"^noted$",
    r"^right$",
    r"^i\s*see$",
    r"^no\s*problem$",
    r"^no\s*worries$",
    r"^np$",
    r"^hmm+$",
    r"^ohh*$",
    r"^ah+$",
    r"^k$",
    r"^kk$",
]

THANKS_RESPONSE = (
    "You're welcome! 😊 "
    "If you have any other questions, feel free to ask. "
    "I'm here to help!"
)

BYE_RESPONSE = (
    "Goodbye! 👋 Have a great day. "
    "Feel free to come back anytime you need help!"
)

ACKNOWLEDGEMENT_RESPONSE = (
    "Got it! 👍 If you need anything else, "
    "just let me know. I'm here to help!"
)


def _matches(text: str, patterns: list) -> bool:
    """Check if text matches any of the given regex patterns."""
    return any(re.fullmatch(p, text) for p in patterns)


def get_greeting_response(message: str) -> str | None:
    """
    Returns a friendly response if the user message is a
    greeting, thanks, goodbye, or casual acknowledgement.
    Otherwise returns None (so the message enters the AI pipeline).
    """

    text = message.strip().lower()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text).strip()

    if not text:
        return None

    if _matches(text, GREETING_PATTERNS):
        return GREETING_RESPONSE

    if _matches(text, THANKS_PATTERNS):
        return THANKS_RESPONSE

    if _matches(text, BYE_PATTERNS):
        return BYE_RESPONSE

    if _matches(text, ACKNOWLEDGEMENT_PATTERNS):
        return ACKNOWLEDGEMENT_RESPONSE

    return None

