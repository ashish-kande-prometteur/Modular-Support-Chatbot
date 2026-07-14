import os

from dotenv import load_dotenv
from openai import OpenAI

from app.retrieval.search import search

load_dotenv()


OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini"
)

HIGH_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "HIGH_CONFIDENCE_THRESHOLD",
        0.35
    )
)

MEDIUM_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "MEDIUM_CONFIDENCE_THRESHOLD",
        0.50
    )
)

LOW_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "LOW_CONFIDENCE_THRESHOLD",
        0.65
    )
)

TOP_K_RESULTS = int(
    os.getenv(
        "TOP_K_RESULTS",
        5
    )
)


client = OpenAI(
    api_key=OPENAI_API_KEY
)


SYSTEM_PROMPT = """
You are an AI customer support assistant.

Your job is to answer customer questions using historical support cases.

Rules:
- Provide natural, concise, and professional responses.
- Never mention ticket numbers.
- Never mention internal support notes.
- Summarize common resolutions from similar historical cases.
- If the information is insufficient, politely ask the customer to contact support.
- Do not invent policies or procedures that are not present in the context.
"""


def build_context(results):

    context_parts = []

    for (
        ticket_number,
        issue,
        resolution,
        distance
    ) in results:

        context_parts.append(
            f"""
Issue:
{issue}

Resolution:
{resolution or "No resolution available"}
"""
        )

    return "\n----------------------\n".join(
        context_parts
    )


def calculate_confidence(
    best_distance: float
):
    """
    Lower distance means higher confidence.
    """

    if best_distance <= HIGH_CONFIDENCE_THRESHOLD:
        return "HIGH"

    if best_distance <= MEDIUM_CONFIDENCE_THRESHOLD:
        return "MEDIUM"

    if best_distance <= LOW_CONFIDENCE_THRESHOLD:
        return "LOW"

    return "VERY_LOW"


def get_ai_response(
    user_query: str
):

    results = search(
        query=user_query,
        top_k=TOP_K_RESULTS
    )

    if not results:
        return {
            "answer": (
                "I couldn't find any relevant "
                "historical cases for your query. "
                "Please contact customer support "
                "for further assistance."
            ),
            "confidence": 0,
            "confidence_level": "NO_MATCH"
        }

    best_distance = results[0][3]

    confidence_level = calculate_confidence(
        best_distance
    )

    if confidence_level == "VERY_LOW":
        return {
            "answer": (
                "I couldn't find a similar issue "
                "in our historical support records. "
                "Please provide more details or "
                "contact customer support for "
                "further assistance."
            ),
            "confidence": round(
                1 - best_distance,
                2
            ),
            "confidence_level": confidence_level
        }

    context = build_context(
        results
    )

    prompt = f"""
Historical Support Cases:

{context}

Customer Question:
{user_query}

Generate a customer-friendly answer based only on the historical support cases.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "answer":
            response.choices[0]
            .message.content,

        "confidence":
            round(
                1 - best_distance,
                2
            ),

        "confidence_level":
            confidence_level
    }
