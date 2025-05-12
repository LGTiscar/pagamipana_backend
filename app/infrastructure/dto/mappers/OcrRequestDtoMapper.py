from app.domain.models.OcrRequest import OcrRequest
from app.infrastructure.dto.OcrRequestDTO import OcrRequestDTO


class OcrRequestDtoMapper:
    @staticmethod
    def to_domain(request_dto: OcrRequestDTO) -> OcrRequest:
        return OcrRequest(
            image=request_dto.image
        )