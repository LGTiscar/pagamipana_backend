
class OcrResponse:
    def __init__(self, ocr_response: dict) -> None:
        self.ocr_response = ocr_response

    def to_dict(self) -> dict:
        return self.ocr_response