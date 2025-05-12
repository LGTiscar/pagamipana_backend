from app.domain.interfaces.OcrClient import OcrClient


class OcrService:

    def __init__(self, ocr_service: OcrClient):
        self.ocr_service = ocr_service

    def get_analysis(self, image: str) -> dict:
        return self.ocr_service.get_analysis(image)