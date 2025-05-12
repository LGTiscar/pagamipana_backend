from abc import ABC


class OcrInput(ABC):
    def __init__(
        self,
        system_prompt,
    ):
        self.system_prompt = system_prompt

    @staticmethod
    def build(**kwargs) -> "OcrInput":
        return OcrInput(**kwargs)

    def to_dict(self) -> dict:
        return {
            "system_prompt": self.system_prompt,
        }
