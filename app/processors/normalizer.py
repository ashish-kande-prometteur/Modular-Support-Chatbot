class TicketNormalizer:

    @staticmethod
    def normalize(ticket):

        return {
            "ticket_id": ticket.get("id"),
            "subject": ticket.get("subject"),
            "status": ticket.get("status"),
            "conversation": ticket.get(
                "conversation",
                []
            )
        }

class IssueExtractor:

    @staticmethod
    def extract_issue(ticket):

        subject = ticket["subject"]

        if subject:
            return subject

        return "Unknown Issue"
    

class ResolutionExtractor:

    @staticmethod
    def extract_resolution(ticket):

        conversations = ticket.get(
            "conversation",
            []
        )

        agent_messages = []

        for msg in conversations:

            author = msg.get(
                "author",
                {}
            )

            if author.get(
                "type"
            ) == "AGENT":

                content = msg.get(
                    "content",
                    ""
                )

                if content:
                    agent_messages.append(
                        content
                    )

        if agent_messages:
            return agent_messages[-1]

        return None
    
