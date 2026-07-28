import requests

from bs4 import BeautifulSoup

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)


def clean_html(html: str) -> str:
    """
    Remove navigation, footer and other
    non-content sections.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup(
        [
            "nav",
            "header",
            "footer",
            "script",
            "style",
            "aside"
        ]
    ):
        tag.decompose()

    return soup.get_text(
        separator="\n",
        strip=True
    )


def split_into_chunks(
    text: str
):
    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300
        )
    )

    return splitter.split_text(
        text
    )


def load_website_pages(
    urls: list[str]
):
    documents = []

    for url in urls:

        try:
            response = requests.get(
                url,
                timeout=10
            )

            response.raise_for_status()

            clean_text = clean_html(
                response.text
            )

            chunks = split_into_chunks(
                clean_text
            )

            for idx, chunk in enumerate(
                chunks
            ):

                documents.append(
                    {
                        "ticket_id":
                            None,

                        "ticket_number":
                            None,

                        "issue":
                            f"Website content from {url}",

                        "resolution":
                            chunk,

                        "status":
                            None,

                        "channel":
                            None,

                        "source":
                            "website",

                        "ref_id":
                            f"{url}#chunk_{idx}",

                        "url":
                            url
                    }
                )

        except Exception as e:
            print(
                f"Failed to ingest {url}: {e}"
            )

    return documents