from abc import ABC, abstractmethod


class UseCaseInterface(ABC):
    @staticmethod
    @abstractmethod
    def execute(*args, **kwargs):
        pass
