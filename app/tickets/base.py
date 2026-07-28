from abc import ABC, abstractmethod


class TicketProvider(ABC):

    @abstractmethod
    def create_ticket(
        self,
        payload: dict
    ) -> dict:
        pass