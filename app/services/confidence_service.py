from typing import Optional

from app.core.config import settings


class ConfidenceService:
    """
    Evaluates chatbot confidence using:
    - Source (RAG / DATABASE / TICKET)
    - Vector distance
    - Context relevance

    Lower vector distance = Better match.
    """

    @classmethod
    def evaluate(
        cls,
        source: str,
        vector_distance: Optional[float] = None,
        context_relevant: Optional[bool] = None,
    ) -> dict:

        source = source.upper()

        # -----------------------------
        # RAG
        # -----------------------------
        if source == "RAG":

            if not context_relevant:
                return cls._response(
                    confidence=0.0,
                    level="LOW",
                    source=source,
                    reason="Context is not relevant.",
                )

            if vector_distance is None:
                return cls._response(
                    confidence=0.5,
                    level="MEDIUM",
                    source=source,
                    reason="Vector distance unavailable.",
                )

            confidence = round(max(0.0, min(1.0, 1 - vector_distance)), 2)

            if vector_distance <= settings.HIGH_CONFIDENCE_THRESHOLD:
                level = "HIGH"

            elif vector_distance <= settings.MEDIUM_CONFIDENCE_THRESHOLD:
                level = "MEDIUM"

            elif vector_distance <= settings.LOW_CONFIDENCE_THRESHOLD:
                level = "LOW"

            else:
                level = "NO_MATCH"

            return cls._response(
                confidence=confidence,
                level=level,
                source=source,
                reason=f"Vector distance = {vector_distance:.3f}",
            )

        # -----------------------------
        # DATABASE
        # -----------------------------
        if source == "DATABASE":
            return cls._response(
                confidence=0.80,
                level="HIGH",
                source=source,
                reason="Structured database response.",
            )

        # -----------------------------
        # TICKET
        # -----------------------------
        if source == "TICKET":
            return cls._response(
                confidence=0.0,
                level="LOW",
                source=source,
                reason="Escalated to support.",
            )

        return cls._response(
            confidence=0.0,
            level="UNKNOWN",
            source=source,
            reason="Unknown response source.",
        )

    @staticmethod
    def _response(
        confidence: float,
        level: str,
        source: str,
        reason: str,
    ) -> dict:
        return {
            "confidence": confidence,
            "confidence_level": level,
            "source": source,
            "reason": reason,
        }
    