from abc import ABC,abstractmethod

from app.infrastructure.ABCSingletonMeta import ABCSingletonMeta


class OcrClient(ABC, metaclass=ABCSingletonMeta):

    @abstractmethod
    def get_analysis(self, image: str) -> dict:
        pass