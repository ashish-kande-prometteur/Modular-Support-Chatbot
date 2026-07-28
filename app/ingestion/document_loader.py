import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"


DOCUMENT_FILES = [
    (
        "frequently_questions.json",
        "faq"
    ),
    (
        "ftimerbet_betting_rules.json",
        "betting_rules"
    ),
    (
        "Privacy_Policy.json",
        "privacy_policy"
    ),
    (
        "responsible_gaming.json",
        "responsible_gaming"
    ),
    (
        "terms_conditions.json",
        "terms_conditions"
    )
]


def load_document_chunks():

    chunks = []

    for filename, source_type in DOCUMENT_FILES:

        file_path = DATA_DIR / filename

        if not file_path.exists():
            continue

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if source_type == "faq":

            chunks.extend(
                process_faq(
                    data
                )
            )

        elif source_type == "betting_rules":

            chunks.extend(
                process_betting_rules(
                    data
                )
            )

        elif source_type == "responsible_gaming":

            chunks.extend(
                process_responsible_gaming(
                    data
                )
            )

        else:

            chunks.extend(
                process_generic_document(
                    data,
                    source_type
                )
            )

    return chunks


def process_faq(data):

    chunks = []

    categories = data.get(
        "categories",
        {}
    )

    for category, items in categories.items():

        for item in items:

            answer = item.get(
                "answer"
            )

            if isinstance(
                answer,
                dict
            ):
                answer = json.dumps(
                    answer,
                    ensure_ascii=False
                )

            chunks.append(
                {
                    "source":
                        "faq",

                    "document":
                        "frequently_questions",

                    "question":
                        item.get(
                            "question"
                        ),

                    "content":
                        f"""
Question:
{item.get('question')}

Answer:
{answer}
"""
                }
            )

    return chunks


def process_betting_rules(data):

    content = data.get(
        "content",
        ""
    )

    paragraphs = content.split(
        "\n\n"
    )

    chunks = []

    chunk_size = 5

    for i in range(
        0,
        len(paragraphs),
        chunk_size
    ):

        chunk_text = "\n\n".join(
            paragraphs[
                i:i + chunk_size
            ]
        )

        chunks.append(
            {
                "source":
                    "betting_rules",

                "document":
                    "ftimerbet_betting_rules",

                "chunk_id":
                    i // chunk_size,

                "content":
                    chunk_text
            }
        )

    return chunks


def process_responsible_gaming(data):

    chunks = []

    categories = data.get(
        "categories",
        {}
    )

    for category_name, sections in categories.items():

        for section in sections:

            title = section.get(
                "title",
                ""
            )

            details = section.get(
                "details",
                []
            )

            if isinstance(
                details,
                list
            ):
                details_text = "\n".join(
                    details
                )
            else:
                details_text = str(
                    details
                )

            chunks.append(
                {
                    "source":
                        "responsible_gaming",

                    "document":
                        "anjouan_compliance",

                    "category":
                        category_name,

                    "section":
                        title,

                    "content":
                        f"""
Category:
{category_name}

Section:
{title}

Details:
{details_text}
"""
                }
            )

    return chunks


def process_generic_document(
    data,
    source_type
):

    chunks = []

    if isinstance(
        data,
        dict
    ):

        for key, value in data.items():

            chunks.append(
                {
                    "source":
                        source_type,

                    "section":
                        key,

                    "content":
                        json.dumps(
                            value,
                            ensure_ascii=False
                        )
                }
            )

    return chunks