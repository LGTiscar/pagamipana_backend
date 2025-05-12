from fastapi import FastAPI, Body, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import logging
import base64
from io import BytesIO
from PIL import Image

from app.application.v1.GetOcrAnalysisUseCase import GetOcrAnalysisUseCase
from app.infrastructure.dto.OcrRequestDTO import OcrRequestDTO
from app.infrastructure.dto.mappers.OcrRequestDtoMapper import OcrRequestDtoMapper
from app.infrastructure.rest.clients.GeminiClient import GeminiClient
from app.domain.models.Exceptions.ApiKeyNotFoundException import ApiKeyNotFoundException
import os
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
    allow_methods=["GET", "POST"],  # Limitar a solo los métodos que necesitas
    allow_headers=["Content-Type", "Authorization"],  # Limitar a solo los headers necesarios
)

@app.get("/")
def read_root():
    logger.info("Endpoint raíz llamado")
    return {"message": "Gemini API Proxy Service"}

# @app.post("/api/ocr/generate")
# def generate_content(request: dict = Body(...)) -> dict:
#     try:
#         logger.info("Recibida solicitud de análisis OCR")
        
#         if "image" not in request or not request.get("image"):
#             logger.error("No se proporcionó una imagen en la solicitud")
#             raise HTTPException(status_code=400, detail="La imagen es requerida")
            
#         request_dto = OcrRequestDTO().from_rest_input(request)
#         image: str = OcrRequestDtoMapper.to_domain(request_dto).image
#         gemini_client = GeminiClient()
#         result = GetOcrAnalysisUseCase(gemini_client).execute(image)
#         response = result.to_dict()
        
#         logger.info(f"Análisis OCR completado: {response}")

#         return response
       
    
#     except ApiKeyNotFoundException as e:
#         logger.critical(f"API key no encontrada: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error de configuración: API key no encontrada")
#     except Exception as e:
#         logger.error(f"Error general: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/api/ocr/generate")
async def generate_content_file(file: UploadFile = File(...)) -> dict:
    try:
        logger.info("Recibida solicitud de análisis OCR (método archivo)")
        
        image_contents = await file.read()        
        img = Image.open(BytesIO(image_contents))
        
        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG", quality=70)
        compressed_image = output_buffer.getvalue()
        
        base64_image = base64.b64encode(compressed_image).decode('utf-8')
        
        gemini_client = GeminiClient()
        result = GetOcrAnalysisUseCase(gemini_client).execute(base64_image)
        response = result.to_dict()
        
        logger.info(f"Análisis OCR completado (método archivo): {response}")
        return response
        
    except ApiKeyNotFoundException as e:
        logger.critical(f"API key no encontrada: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de configuración: API key no encontrada")
    except Exception as e:
        logger.error(f"Error al procesar archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")
