import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.retrieval.search import search
from app.security.pii_guard import redact
from app.services.database_service import DatabaseService
from app.services.raise_ticket import create_unanswered_query
from sqlalchemy.orm import Session
from app.services.handoff_service import HandoffService

load_dotenv()


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.1-8b-instant"
)

db_service = DatabaseService()

TOP_K_RESULTS = int(
    os.getenv(
        "TOP_K_RESULTS",
        5
    )
)


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
You are an AI customer support assistant.

You answer questions ONLY using the retrieved context provided.

The context may contain:
- Historical support tickets
- FAQ documents
- Betting rules
- Terms and conditions
- Privacy policy
- Responsible gaming documents
- Website content

Rules:
- Use only information present in the provided context.
- Do not generate generic answers.
- If the context contains policy details, explicitly mention those details.
- If the answer is not present in the context, say that the information is unavailable.
- Never invent policies or procedures.
- Never use external knowledge.
- Prefer quoting or closely paraphrasing the retrieved content.
"""


RELEVANCE_SYSTEM_PROMPT = """
You are a strict relevance classifier for a customer support system.
You will be given retrieved context and a customer question.
Decide if the context contains enough information to directly and
confidently answer the question.

Reply with exactly one word: YES or NO.
Do not explain your reasoning. Do not add punctuation.
"""


def _describe_tables() -> str:
    lines = []

    for table_name, meta in db_service.TABLES.items():
        columns = ", ".join(meta["columns"])
        lines.append(
            f"- {table_name} (columns: {columns}) -> {meta['display']}"
        )

    return "\n".join(lines)


DB_QUERY_SYSTEM_PROMPT = f"""
You convert a customer support question into a structured database query.

Available tables:
{_describe_tables()}

Decide:
1. "table": the single most relevant table name from the list above,
   or null if none of the tables are relevant to the question.
2. "operation":
   - "count"  -> the user wants a total number of records
   - "list"   -> the user wants the names/items listed
   - "search" -> the user wants details about one specific named item
   - "none"   -> the question does not relate to any table above
3. "value": only when operation is "search", the specific name or
   keyword being asked about (e.g. a provider name, a country name,
   a promotion title). Otherwise null.

Respond with ONLY valid JSON, no extra text, no markdown fences,
in exactly this shape:
{{"table": "<table_name_or_null>", "operation": "<count|list|search|none>", "value": "<value_or_null>"}}
"""


# ------------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------------

def generate_db_query_with_ai(user_query: str):
    """
    Ask the model to turn the user's natural-language question into a
    structured database query (table + operation + optional value),
    instead of relying on brittle keyword matching.
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": DB_QUERY_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    raw = response.choices[0].message.content

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

    table = parsed.get("table")
    operation = parsed.get("operation")
    value = parsed.get("value")

    if not table or table not in db_service.TABLES:
        return None

    if operation not in ("count", "list", "search"):
        return None

    if operation == "search" and not value:
        return None

    return {
        "type": operation,
        "table": table,
        "value": value
    }


def handle_database_query(
    user_query: str,
):
    """
    Handle database-only questions using an AI-generated query
    (table + operation) derived from the user's question.
    """

    intent = generate_db_query_with_ai(
        user_query
    )

    if not intent:
        return None

    if intent["type"] == "count":

        return db_service.count(
            intent["table"]
        )

    if intent["type"] == "list":

        return db_service.list(
            intent["table"]
        )

    if intent["type"] == "search":

        return db_service.search(
            intent["table"],
            intent["value"]
        )

    return None


def generate_database_response(
    database_result,
    user_query: str
):
    result_type = database_result.get("type")

    prompt = f"""
Database Result:

{database_result}

Customer Question:

{user_query}

Instructions:
- Answer ONLY using the database result above.
- The result type is "{result_type}".
- If the type is "count": state the total number clearly, in one sentence.
- If the type is "list": you MUST list every single item in "rows" as
  bullet points. Do NOT summarize the list as just a total count -
  the user explicitly wants the names, not just how many there are.
- If the type is "search" or "record": summarize the matching
  record(s) in "rows"/"record" in plain language.
- Do not invent information that is not present in the database result.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful customer support assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "answer": response.choices[0].message.content,
        "confidence": 1.0,
        "confidence_level": "DATABASE",
        "source": "DATABASE"
    }


def create_support_ticket(
    db: Session,
    session_id,
    user_query: str,
    trigger_type: str,
    bot_answer: str = None,
    confidence: float = 0.0,
):
    """
    Creates an unanswered query record and initiates the
    human handoff workflow.

    Flow:
        1. Store unanswered query
        2. Mark chat session for handoff
        3. Find available agents
        4. Return ticket + handoff details
    """

    ticket_response = None
    handoff = None

    if (
        os.getenv(
            "ENABLE_UNANSWERED_QUERY_LOGGING",
            "true",
        ).lower()
        == "true"
    ):

        try:

            # -----------------------------------------
            # Create unanswered query record
            # -----------------------------------------
            ticket_response = create_unanswered_query(
                {
                    "user_query": user_query,
                    "bot_answer": bot_answer,
                    "trigger_type": trigger_type,
                    "confidence": confidence,
                }
            )

            # -----------------------------------------
            # Start human handoff
            # -----------------------------------------
            handoff = HandoffService.request_handoff(
                db=db,
                session_id=session_id,
                reason=trigger_type,
            )

            print("\n" + "=" * 80)
            print("SUPPORT SESSION CREATED")
            print(f"Session ID : {handoff['session_id']}")
            print(f"Support URL: {handoff['support_url']}")
            print("=" * 80 + "\n")

        except Exception as exc:

            print(
                "Failed to create support ticket:",
                exc,
            )

    return {
        "answer": (
            "I couldn't find a reliable answer for your issue. "
            "Your request has been forwarded to our support team. "
            "An available support agent will join the conversation shortly."
        ),
        "confidence": 0,
        "confidence_level": "NO_MATCH",
        "source": "TICKET",
        "ticket": ticket_response,
        "handoff": handoff,
    }

def is_database_result_empty(database_result) -> bool:
    """
    A DatabaseService call always returns a dict (never None) once a
    table is matched, even when nothing was actually found - e.g.
    search()/list() return rows=[] rather than None. Treat those as
    "not found" so the flow falls through to ticket creation instead
    of asking the LLM to describe an empty result set.
    """

    if not database_result:
        return True

    result_type = database_result.get("type")

    if result_type == "count":
        # A count of 0 is still a real, factual answer - not a miss.
        return False

    if result_type in ("list", "search"):
        return not database_result.get("rows")

    if result_type == "record":
        return database_result.get("record") is None

    return True


def handle_database_or_ticket(
    db,
    session_id,
    user_query,
    trigger_type,
    bot_answer=None,
    confidence=0.0,
):
    """
    Shared fallback used whenever the vector search / RAG path
    can't confidently answer the question:
      - try the structured database
      - if nothing found there either, raise a support ticket
    """

    database_result = handle_database_query(
        user_query
    )

    if database_result and not is_database_result_empty(
        database_result
    ):
        return generate_database_response(
            database_result,
            user_query
        )
    print("creating ticket")
    return create_support_ticket(
        db=db,
        session_id=session_id,
        user_query=user_query,
        trigger_type=trigger_type,
        bot_answer=bot_answer,
        confidence=confidence,
    )


# ------------------------------------------------------------------
# RAG helpers
# ------------------------------------------------------------------

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
Knowledge Source:
{issue}

Content:
{resolution}
"""
        )

    return "\n----------------------\n".join(
        context_parts
    )


def context_can_answer(
    context: str,
    user_query: str
) -> bool:
    """
    Ask the LLM whether the retrieved context is actually
    sufficient to answer the user's question, instead of
    relying purely on vector-distance thresholds.
    """

    check_prompt = f"""
Retrieved Context:

{context}

Customer Question:

{user_query}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": RELEVANCE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": check_prompt
            }
        ]
    )

    verdict = (
        response.choices[0]
        .message.content
        .strip()
        .upper()
    )

    return verdict.startswith("YES")


def generate_rag_answer(
    context: str,
    safe_query: str,
    best_distance: float
):
    prompt = f"""
    Retrieved Context:

    {context}

    Customer Question:
    {safe_query}

    Instructions:
    - Answer ONLY using the retrieved context above.
    - If privacy policies, terms, FAQ or rules are provided in the context,
    include the relevant details in your answer.
    - Do not use general knowledge.
    - Do not invent information.
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,
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

        "confidence_level": "RAG",
        "source": "RAG"
    }


# ------------------------------------------------------------------
# Main entrypoint
# ------------------------------------------------------------------

def get_ai_response(
    db,
    session_id,
    user_query,
):
    """
    Flow:

    User Query
        -> Vector Search
        -> No results?          -> Database -> (found -> DB answer | not found -> Ticket)
        -> Results found        -> Build Context
                                 -> Ask LLM "can this context answer the question?"
                                     -> YES -> Return RAG answer
                                     -> NO  -> Database -> (found -> DB answer | not found -> Ticket)
    """

    results = search(
        query=user_query,
        top_k=TOP_K_RESULTS
    )

    # ------------------------------------------------------------
    # No vector search results at all -> go straight to database
    # ------------------------------------------------------------
    if not results:

        return handle_database_or_ticket(
            db=db,
            session_id=session_id,
            user_query=user_query,
            trigger_type="LOW_CONTEXT_RELEVANCE",
        )

    # ------------------------------------------------------------
    # We have candidate matches -> build + sanitize context
    # ------------------------------------------------------------
    context = build_context(
        results
    )

    context = redact(
        context
    )

    safe_query = redact(
        user_query
    )

    # ------------------------------------------------------------
    # Let the LLM judge whether the context is actually usable
    # ------------------------------------------------------------
    if context_can_answer(
        context,
        safe_query
    ):

        best_distance = results[0][3]

        return generate_rag_answer(
            context,
            safe_query,
            best_distance
        )

    # ------------------------------------------------------------
    # Context wasn't good enough -> fall back to database / ticket
    # ------------------------------------------------------------
    return handle_database_or_ticket(
        db=db,
        session_id=session_id,
        user_query=user_query,
        trigger_type="LOW_CONTEXT_RELEVANCE",
    )
