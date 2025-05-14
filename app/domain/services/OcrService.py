from app.domain.interfaces.OcrClient import OcrClient


class OcrService:

    def __init__(self, ocr_client: OcrClient):
        self.ocr_client = ocr_client

    def get_analysis(self, image_bytes: bytes, image_mime_type: str) -> dict:
        return self.ocr_client.get_analysis(image_bytes=image_bytes, image_mime_type=image_mime_type)