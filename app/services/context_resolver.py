import os
import re

from dotenv import load_dotenv

from app.services.conversation_service import ConversationService

load_dotenv()

HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", 6))

# ----------------------------------------------------------
# Words that indicate the user is referring to something
# from the previous conversation (pronouns, demonstratives,
# anaphoric references).
# ----------------------------------------------------------
REFERENCE_WORDS = {
    "it", "its", "this", "that", "those", "these",
    "them", "they", "their", "previous", "above",
    "mentioned", "former", "latter",
}

# Compiled once — matches whole words only, case-insensitive.
_REFERENCE_PATTERN = re.compile(
    r"\b(" + "|".join(REFERENCE_WORDS) + r")\b",
    re.IGNORECASE,
)

# Short / vague queries that almost certainly need context
# even if they don't contain a classic pronoun.
#   e.g. "how much?", "what are the rules?", "tell me more"
_VAGUE_PATTERNS = re.compile(
    r"\b("
    r"tell me more"
    r"|explain more"
    r"|more details"
    r"|more about"
    r"|what about"
    r"|how much"
    r"|how many"
    r"|what are the rules"
    r"|what are the requirements"
    r"|what documents"
    r"|which one"
    r")\b",
    re.IGNORECASE,
)

# Common filler words to strip when extracting the topic
# from a previous user question.
_STOP_WORDS = {
    "what", "is", "are", "was", "were", "the", "a", "an",
    "of", "in", "on", "to", "for", "and", "or", "do", "does",
    "did", "can", "could", "will", "would", "how", "tell",
    "me", "about", "please", "i", "my", "your", "you",
    "show", "give", "list", "explain", "describe", "know",
    "want", "need", "have", "has", "had", "be", "been",
    "am", "with", "from", "by", "at", "any", "some",
    "there", "here", "also", "all", "get", "got",
}


def _needs_context(query: str) -> bool:
    """
    Return True if the query contains pronoun/reference words
    or vague phrases that depend on prior conversation context.
    """
    return bool(
        _REFERENCE_PATTERN.search(query)
        or _VAGUE_PATTERNS.search(query)
    )


def _extract_topic(text: str) -> str:
    """
    Extract meaningful keywords from a sentence by removing
    common stop/filler words and punctuation.

    Examples:
        "what is the welcome bonus?"  →  "welcome bonus"
        "Tell me about withdrawal."   →  "withdrawal"
        "List all casino providers."  →  "casino providers"
    """
    # Remove punctuation
    cleaned = re.sub(r"[^\w\s]", "", text)

    words = [
        w for w in cleaned.split()
        if w.lower() not in _STOP_WORDS
    ]

    return " ".join(words)


def _extract_last_user_topic(history: list) -> str:
    """
    Walk backwards through the OpenAI-style message list
    and return the key topic from the most recent user
    message.
    """
    for msg in reversed(history):
        if msg["role"] == "user":
            topic = _extract_topic(msg["content"])
            if topic:
                return topic
    return ""


def _extract_last_assistant_topic(history: list) -> str:
    """
    Walk backwards and extract the topic from the first
    sentence of the most recent assistant response.
    """
    for msg in reversed(history):
        if msg["role"] == "assistant":
            text = msg["content"].strip()
            first_sentence = re.split(r"[.\n]", text, maxsplit=1)[0]
            topic = _extract_topic(first_sentence)
            if topic:
                return topic
    return ""


def _substitute_references(query: str, topic: str) -> str:
    """
    Replace pronoun/reference words in the query with the
    extracted topic.

    Examples:
        query="any rules for this", topic="welcome bonus"
        → "any rules for welcome bonus"

        query="how is it calculated", topic="RTP"
        → "how is RTP calculated"
    """
    resolved = _REFERENCE_PATTERN.sub(topic, query)

    # Clean up any double spaces from substitution
    resolved = re.sub(r"\s{2,}", " ", resolved).strip()

    return resolved


def _append_topic(query: str, topic: str) -> str:
    """
    For vague queries that don't contain a direct pronoun to
    substitute, append the topic for context.

    Example:
        query="what are the rules", topic="welcome bonus"
        → "what are the rules for welcome bonus"
    """
    return f"{query} for {topic}"


def resolve_query(
    db,
    session_id,
    user_query: str,
) -> str:
    """
    Rewrite the user's latest message into a self-contained
    search query by resolving pronouns / references against
    the recent conversation history.

    This is a **rule-based** implementation — no LLM call is
    made.  If the query already looks self-contained, it is
    returned unchanged.

    The function signature is identical to the previous
    LLM-based version, so callers don't need any changes.
    """

    # ----------------------------------------------------------
    # 1. Quick check — does the query even need resolution?
    # ----------------------------------------------------------
    has_pronoun = bool(_REFERENCE_PATTERN.search(user_query))
    has_vague = bool(_VAGUE_PATTERNS.search(user_query))

    if not has_pronoun and not has_vague:
        return user_query

    # ----------------------------------------------------------
    # 2. Fetch recent conversation history from the database
    # ----------------------------------------------------------
    conversation_service = ConversationService(db)

    history = conversation_service.format_for_llm(
        session_id=session_id,
        limit=HISTORY_LIMIT,
    )

    # The current user message has already been saved to the DB
    # (in chat.py) BEFORE this function is called, so it will
    # appear as the last entry in history.  Strip it so we only
    # look at genuinely *previous* messages for context.
    while (
        history
        and history[-1]["role"] == "user"
        and history[-1]["content"].strip().lower()
            == user_query.strip().lower()
    ):
        history.pop()

    # First message in the session — nothing to resolve against.
    if not history:
        return user_query

    # ----------------------------------------------------------
    # 3. Extract the topic from previous conversation
    # ----------------------------------------------------------
    topic = (
        _extract_last_user_topic(history)
        or _extract_last_assistant_topic(history)
    )

    if not topic:
        return user_query

    # ----------------------------------------------------------
    # 4. Resolve the query
    # ----------------------------------------------------------
    if has_pronoun:
        # Replace "it", "this", "that" etc. with the topic
        resolved = _substitute_references(user_query, topic)
    else:
        # Vague query — append topic for context
        resolved = _append_topic(user_query, topic)

    print(
        f"\n[ContextResolver] "
        f"Original : {user_query}\n"
        f"[ContextResolver] "
        f"Topic    : {topic}\n"
        f"[ContextResolver] "
        f"Resolved : {resolved}\n"
    )

    return resolved

