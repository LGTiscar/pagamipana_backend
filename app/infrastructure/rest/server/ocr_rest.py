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

# Cargar variables de entorno
load_dotenv()

# Configurar logging más detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Asegurar que los logs van a stdout para Vercel
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_path = request.url.path
    request_method = request.method
    logger.info(f"Recibida solicitud: {request_method} {request_path}")
    
    try:
        # Intenta leer el body si es relevante
        if request_method in ["POST", "PUT"]:
            try:
                # Clonar el body para poder leerlo
                body = await request.body()
                if body and len(body) > 0:
                    # Si el body es una imagen, solo loggea el tamaño
                    if b'image' in body or b'file' in body or len(body) > 1000:
                        logger.info(f"Body recibido con {len(body)} bytes (imagen/archivo)")
                    else:
                        # Para bodies pequeños, intentamos mostrar el contenido
                        try:
                            body_str = body.decode()
                            # Ocultar información sensible
                            if len(body_str) < 1000:  # Solo log para bodies pequeños
                                logger.info(f"Body recibido: {body_str[:200]}...")
                        except:
                            logger.info("Body no decodificable como texto")
            except Exception as e:
                logger.warning(f"No se pudo leer el body: {e}")
        
        # Procesar la petición
        response = await call_next(request)
        logger.info(f"Respuesta enviada: {response.status_code}")
        return response
    except Exception as e:
        # Log detallado de cualquier error en el middleware
        logger.error(f"Error en middleware: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.get("/")
def read_root():
    logger.info("Endpoint raíz llamado")
    return {"message": "Gemini API Proxy Service"}


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
            # Procesar la imagen
            img = Image.open(BytesIO(image_contents))
            logger.info(f"Imagen abierta correctamente: {img.format} {img.size}")
            
            # Convertir a JPEG con compresión
            output_buffer = BytesIO()
            img.save(output_buffer, format="JPEG", quality=70)
            compressed_image = output_buffer.getvalue()
            logger.info(f"Imagen comprimida correctamente, nuevo tamaño: {len(compressed_image)} bytes")
            
            # Convertir a base64 para el cliente Gemini
            base64_image = base64.b64encode(compressed_image).decode('utf-8')
            logger.info(f"Imagen convertida a base64, tamaño: {len(base64_image)} caracteres")
            
            # Verificar la API key antes de llamar al cliente
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.critical("API key de Gemini no encontrada en variables de entorno")
                raise ApiKeyNotFoundException("API key de Gemini no encontrada")
            
            logger.info(f"API key encontrada y tiene {len(api_key)} caracteres")
            
            # Procesar con el caso de uso existente
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
            # Log detallado del error
            error_traceback = traceback.format_exc()
            logger.error(f"Error al procesar archivo: {str(e)}")
            logger.error(f"Traceback completo: {error_traceback}")
            raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")
            
    except HTTPException:
        # Re-lanzar HTTPExceptions para mantener el status code
        raise
    
    except Exception as e:
        # Captura cualquier otra excepción no manejada
        error_traceback = traceback.format_exc()
        logger.error(f"Excepción no manejada en generate_content_file: {str(e)}")
        logger.error(f"Traceback completo: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
