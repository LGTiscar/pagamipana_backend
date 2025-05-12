from app.application.v1.UseCaseInterface import UseCaseInterface
from app.domain.interfaces.OcrClient import OcrClient
from app.domain.models.OcrResponse import OcrResponse
from app.domain.services.OcrService import OcrService


class GetOcrAnalysisUseCase(UseCaseInterface):

    def __init__(self, ocr_service: OcrClient):
        self.ocr_service = ocr_service

    def execute(self, image: str) -> OcrResponse:
        result = OcrService(self.ocr_service).get_analysis(image)

        return OcrResponse(result)
