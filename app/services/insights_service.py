from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage, SenderType
from app.models.chat_session import (
    ChatSession,
    ResolutionType,
)


class InsightsController:

    @staticmethod
    def get_conversation_analytics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        # -----------------------------------------------------
        # Base Session Query
        # -----------------------------------------------------

        session_query = db.query(ChatSession)

        if start_date:
            session_query = session_query.filter(
                ChatSession.created_at >= start_date
            )

        if end_date:
            session_query = session_query.filter(
                ChatSession.created_at <= end_date
            )

        # -----------------------------------------------------
        # Total Conversations
        # -----------------------------------------------------

        total_conversations = session_query.count()

        # -----------------------------------------------------
        # Unique Users
        # -----------------------------------------------------

        unique_users_query = db.query(
            func.count(
                func.distinct(ChatSession.external_user_id)
            )
        )

        if start_date:
            unique_users_query = unique_users_query.filter(
                ChatSession.created_at >= start_date
            )

        if end_date:
            unique_users_query = unique_users_query.filter(
                ChatSession.created_at <= end_date
            )

        unique_users = unique_users_query.scalar() or 0

        # -----------------------------------------------------
        # Resolution Counts
        # -----------------------------------------------------

        ai_resolved = session_query.filter(
            ChatSession.resolution_type
            == ResolutionType.AI_RESOLVED
        ).count()

        human_resolved = session_query.filter(
            ChatSession.resolution_type
            == ResolutionType.HUMAN_RESOLVED
        ).count()

        abandoned = session_query.filter(
            ChatSession.resolution_type
            == ResolutionType.ABANDONED
        ).count()

        # -----------------------------------------------------
        # Ongoing
        #
        # No resolution_type means that the conversation has
        # not reached a final outcome yet.
        # -----------------------------------------------------

        ongoing = session_query.filter(
            ChatSession.resolution_type.is_(None)
        ).count()

        # -----------------------------------------------------
        # Escalated
        #
        # Any session where human handoff was requested.
        # -----------------------------------------------------

        escalated = session_query.filter(
            ChatSession.handoff_requested_at.isnot(None)
        ).count()

        # -----------------------------------------------------
        # AI Resolution Rate
        #
        # AI resolved / all resolved conversations
        #
        # Abandoned and ongoing conversations are excluded.
        # -----------------------------------------------------

        resolved_conversations = (
            ai_resolved + human_resolved
        )

        if resolved_conversations > 0:
            ai_resolution_rate = round(
                (
                    ai_resolved
                    / resolved_conversations
                )
                * 100,
                2,
            )
        else:
            ai_resolution_rate = 0.0

        # -----------------------------------------------------
        # Escalation Rate
        #
        # Escalated / total conversations
        # -----------------------------------------------------

        if total_conversations > 0:
            escalation_rate = round(
                (
                    escalated
                    / total_conversations
                )
                * 100,
                2,
            )
        else:
            escalation_rate = 0.0

        # -----------------------------------------------------
        # AI Response Time Statistics
        #
        # Only AI messages containing response_time_ms
        # are considered.
        # -----------------------------------------------------

        response_time_query = db.query(
            ChatMessage.response_time_ms
        ).filter(
            ChatMessage.sender_type == SenderType.AI,
            ChatMessage.response_time_ms.isnot(None),
        )

        # Apply date filters to AI messages as well.
        if start_date:
            response_time_query = response_time_query.filter(
                ChatMessage.created_at >= start_date
            )

        if end_date:
            response_time_query = response_time_query.filter(
                ChatMessage.created_at <= end_date
            )

        response_times = [
            row[0]
            for row in response_time_query.all()
            if row[0] is not None
        ]

        # -----------------------------------------------------
        # Average Response Time
        # -----------------------------------------------------

        if response_times:
            average_response_time_ms = round(
                sum(response_times)
                / len(response_times),
                2,
            )
        else:
            average_response_time_ms = 0.0

        # -----------------------------------------------------
        # Median Response Time
        # -----------------------------------------------------

        if response_times:
            sorted_times = sorted(response_times)
            count = len(sorted_times)
            middle = count // 2

            if count % 2 == 0:
                median_response_time_ms = round(
                    (
                        sorted_times[middle - 1]
                        + sorted_times[middle]
                    )
                    / 2,
                    2,
                )
            else:
                median_response_time_ms = float(
                    sorted_times[middle]
                )

        else:
            median_response_time_ms = 0.0

        # -----------------------------------------------------
        # P95 Response Time
        #
        # 95% of responses completed within this time.
        # Nearest-rank percentile.
        # -----------------------------------------------------

        if response_times:
            sorted_times = sorted(response_times)

            p95_index = max(
                0,
                int(
                    0.95 * len(sorted_times) + 0.999999
                ) - 1,
            )

            p95_response_time_ms = float(
                sorted_times[p95_index]
            )

        else:
            p95_response_time_ms = 0.0

        # -----------------------------------------------------
        # Response Time Standard Deviation
        # -----------------------------------------------------

        if response_times:
            mean = (
                sum(response_times)
                / len(response_times)
            )

            variance = sum(
                (response_time - mean) ** 2
                for response_time in response_times
            ) / len(response_times)

            response_time_stddev_ms = round(
                variance ** 0.5,
                2,
            )

        else:
            response_time_stddev_ms = 0.0

        # -----------------------------------------------------
        # Average Conversation Length
        #
        # Total messages / total conversations
        # -----------------------------------------------------

        message_count_query = (
            db.query(func.count(ChatMessage.id))
            .join(
                ChatSession,
                ChatMessage.session_id
                == ChatSession.id,
            )
        )

        if start_date:
            message_count_query = (
                message_count_query.filter(
                    ChatSession.created_at >= start_date
                )
            )

        if end_date:
            message_count_query = (
                message_count_query.filter(
                    ChatSession.created_at <= end_date
                )
            )

        total_messages = (
            message_count_query.scalar() or 0
        )

        if total_conversations > 0:
            average_conversation_length = round(
                total_messages
                / total_conversations,
                2,
            )
        else:
            average_conversation_length = 0.0

        # -----------------------------------------------------
        # Response
        # -----------------------------------------------------

        return {
            "total_conversations": total_conversations,
            "unique_users": unique_users,

            "ai_resolved": ai_resolved,
            "human_resolved": human_resolved,
            "abandoned": abandoned,
            "ongoing": ongoing,
            "escalated": escalated,

            "ai_resolution_rate": ai_resolution_rate,
            "escalation_rate": escalation_rate,

            "average_response_time_ms": (
                average_response_time_ms
            ),
            "median_response_time_ms": (
                median_response_time_ms
            ),
            "p95_response_time_ms": (
                p95_response_time_ms
            ),
            "response_time_stddev_ms": (
                response_time_stddev_ms
            ),

            "average_conversation_length": (
                average_conversation_length
            ),
        }