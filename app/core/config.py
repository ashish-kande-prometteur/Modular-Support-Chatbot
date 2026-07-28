import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Application configuration loaded from environment variables.
    """

    # ---------------------------------
    # Confidence Engine
    # ---------------------------------
    HIGH_CONFIDENCE_THRESHOLD = float(
        os.getenv("HIGH_CONFIDENCE_THRESHOLD", 0.35)
    )

    MEDIUM_CONFIDENCE_THRESHOLD = float(
        os.getenv("MEDIUM_CONFIDENCE_THRESHOLD", 0.50)
    )

    LOW_CONFIDENCE_THRESHOLD = float(
        os.getenv("LOW_CONFIDENCE_THRESHOLD", 0.65)
    )

    SUPPORT_PORTAL_URL = os.getenv(
        "SUPPORT_PORTAL_URL",
        "http://localhost:3000",
    )


settings = Settings()
