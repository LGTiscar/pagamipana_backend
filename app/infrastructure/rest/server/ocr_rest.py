from fastapi import FastAPI, Body, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import base64
import sys
import traceback
from io import BytesIO
from PIL import Image
import json

from app.application.v1.GetOcrAnalysisUseCase import GetOcrAnalysisUseCase
from app.infrastructure.dto.OcrRequestDTO import OcrRequestDTO
from app.infrastructure.dto.mappers.OcrRequestDtoMapper import OcrRequestDtoMapper
from app.infrastructure.rest.clients.GeminiClient import GeminiClient
from app.domain.models.Exceptions.ApiKeyNotFoundException import ApiKeyNotFoundException
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gemini API Proxy", description="Backend para interactuar con la API de Gemini")

ALLOWED_ORIGINS = [
    "pagamipana://app",

]


ALLOWED_ORIGINS = list(filter(None, ALLOWED_ORIGINS))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    logger.info("Endpoint raíz llamado")
    return {"message": "Gemini API Proxy Service"}

# todo logs a mi manera
@app.post("/api/ocr/generate")
async def generate_content_file(file: UploadFile = File(...)) -> dict:
    try:
        logger.info(f"Recibida solicitud de análisis OCR (método archivo): {file.filename}")
        
        # Leer y procesar la imagen
        try:
            image_contents = await file.read()
            logger.info(f"Archivo leído correctamente, tamaño: {len(image_contents)} bytes")
        except Exception as e:
            logger.error(f"Error al leer el archivo: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error al leer el archivo: {str(e)}")
        
        try:
            img = Image.open(BytesIO(image_contents))
            logger.info(f"Imagen abierta correctamente: {img.format} {img.size}")
            
            output_buffer = BytesIO()
            img.save(output_buffer, format="JPEG", quality=70)
            compressed_image = output_buffer.getvalue()
            logger.info(f"Imagen comprimida correctamente, nuevo tamaño: {len(compressed_image)} bytes")
        
            base64_image = base64.b64encode(compressed_image).decode('utf-8')
            logger.info(f"Imagen convertida a base64, tamaño: {len(base64_image)} caracteres")
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.critical("API key de Gemini no encontrada en variables de entorno")
                raise ApiKeyNotFoundException("API key de Gemini no encontrada")
            
            logger.info(f"API key encontrada y tiene {len(api_key)} caracteres")
            
            gemini_client = GeminiClient()
            logger.info("Cliente Gemini inicializado correctamente")
            
            result = GetOcrAnalysisUseCase(gemini_client).execute(base64_image)
            logger.info("Caso de uso ejecutado correctamente")
            
            response = result.to_dict()
            logger.info(f"Análisis OCR completado (método archivo): {json.dumps(response)}")
            
            return response
            
        except ApiKeyNotFoundException as e:
            logger.critical(f"API key no encontrada: {str(e)}")
            raise HTTPException(status_code=500, detail="Error de configuración: API key no encontrada")
        
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error al procesar archivo: {str(e)}")
            logger.error(f"Traceback completo: {error_traceback}")
            raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Excepción no manejada en generate_content_file: {str(e)}")
        logger.error(f"Traceback completo: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
