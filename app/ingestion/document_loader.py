import json
from pathlib import Path
import re


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
    chunks = []

    pattern = r'(?=^\d+(?:\.\d+)+\.\s+)'

    chunk_id = 0

    for item in data:

        content = item.get("content", "")

        sections = re.split(pattern, content, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()

            if not section:
                continue

            chunks.append({
                "source": item.get("source", "betting_rules"),
                "document": item.get("document", "ftimerbet_betting_rules"),
                "chunk_id": chunk_id,
                "content": section
            })

            chunk_id += 1

    return chunks

def process_responsible_gaming(data):

    chunks = []

    for item in data:

        chapter = item.get("chapter", {})
        section = item.get("section", {})

        keywords = "\n".join(
            item.get("keywords", [])
        )

        questions = "\n".join(
            item.get("questions", [])
        )

        chunks.append(
            {
                "source": item.get(
                    "source",
                    "responsible_gaming"
                ),

                "document": item.get(
                    "document"
                ),

                "chunk_id": item.get(
                    "id"
                ),

                "content": f"""
Document:
{item.get('document')}

Chapter:
{chapter.get('number')} - {chapter.get('title')}

Section:
{section.get('number')} - {section.get('title')}

Keywords:
{keywords}

Possible Questions:
{questions}

Content:
{item.get('content')}
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