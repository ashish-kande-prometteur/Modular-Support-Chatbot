import re

PATTERNS = {
    "EMAIL": re.compile(
        r"[\w\.-]+@[\w\.-]+\.\w+"
    ),

    "PHONE": re.compile(
        r"\b\d{10,15}\b"
    ),

    "CARD": re.compile(
        r"\b\d{13,19}\b"
    ),

    "ACCOUNT": re.compile(
        r"\b\d{8,20}\b"
    ),

    "UPI": re.compile(
        r"\b[\w\.-]+@[\w]+\b"
    )
}


def redact(text: str):

    if not text:
        return text

    for label, pattern in PATTERNS.items():

        text = pattern.sub(
            f"[{label}_REDACTED]",
            text
        )

    return text