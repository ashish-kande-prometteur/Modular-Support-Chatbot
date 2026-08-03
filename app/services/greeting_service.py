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


def get_greeting_response(message: str) -> str | None:
    """
    Returns a welcome message if the user message is a greeting.
    Otherwise returns None.
    """

    text = message.strip().lower()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    for pattern in GREETING_PATTERNS:
        if re.fullmatch(pattern, text):
            return (
                "👋 Hello! Welcome to FTimer Support.\n\n"
                "I'm here to help you with:\n"
                "• Account & Login\n"
                "• Deposits & Withdrawals\n"
                "• Bonuses & Promotions\n"
                "• Betting Rules\n"
                "• Responsible Gaming\n\n"
                "How may I assist you today?"
            )

    return None
