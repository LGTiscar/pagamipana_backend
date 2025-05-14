from abc import ABC,abstractmethod

from app.infrastructure.ABCSingletonMeta import ABCSingletonMeta


class OcrClient(ABC, metaclass=ABCSingletonMeta):

    @abstractmethod
    def get_analysis(self, image_bytes: bytes, image_mime_type: str) -> dict:
        pass