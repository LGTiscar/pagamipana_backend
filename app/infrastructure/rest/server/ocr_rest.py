from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.application.v1.GetOcrAnalysisUseCase import GetOcrAnalysisUseCase
from app.infrastructure.dto.OcrRequestDTO import OcrRequestDTO
from app.infrastructure.dto.mappers.OcrRequestDtoMapper import OcrRequestDtoMapper
from app.infrastructure.rest.clients.GeminiClient import GeminiClient
from app.domain.models.Exceptions.ApiKeyNotFoundException import ApiKeyNotFoundException
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Gemini API Proxy", description="Backend para interactuar con la API de Gemini")

ALLOWED_ORIGINS = [
    "pagamipana://app",
    "http://localhost:19006",
]

ALLOWED_ORIGINS = list(filter(None, ALLOWED_ORIGINS))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.get("/")
def read_root():
    logger.info("Endpoint raíz llamado")
    return {"message": "Gemini API Proxy Service"}

@app.post("/api/ocr/generate")
def generate_content(request: dict = Body(...)) -> dict:
    try:
        logger.info("Recibida solicitud de análisis OCR")
        
        if "image" not in request or not request.get("image"):
            logger.error("No se proporcionó una imagen en la solicitud")
            raise HTTPException(status_code=400, detail="La imagen es requerida")
            
        request_dto = OcrRequestDTO().from_rest_input(request)
        image: str = OcrRequestDtoMapper.to_domain(request_dto).image
        gemini_client = GeminiClient()
        result = GetOcrAnalysisUseCase(gemini_client).execute(image)
        response = result.to_dict()
        
        logger.info(f"Análisis OCR completado: {response}")

        return response
       
    
    except ApiKeyNotFoundException as e:
        logger.critical(f"API key no encontrada: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de configuración: API key no encontrada")
