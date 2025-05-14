from dotenv import load_dotenv
from app.domain.interfaces.OcrClient import OcrClient
import os
import requests
import logging
import traceback
import json
import time

from app.domain.models.Exceptions.ApiKeyNotFoundException import ApiKeyNotFoundException
from app.infrastructure.llm.OcrTicketInput import OcrTicketInput

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurar logger
logger = logging.getLogger(__name__)

class GeminiClient(OcrClient):
    def __init__(self, model: str = 'gemini-2.0-flash-lite'):
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self.model = model
        logger.info(f"GeminiClient inicializado con modelo: {model}")

    def get_analysis(self, image: str) -> dict:
        logger.info(f"Iniciando análisis con Gemini, modelo {self.model}")
        
        if not GEMINI_API_KEY:
            logger.critical("API key de Gemini no encontrada")
            raise ApiKeyNotFoundException("API key de Gemini no encontrada en variables de entorno")

        # Verificar longitud de la API key
        if len(GEMINI_API_KEY) < 10:
            logger.warning(f"La API key parece ser demasiado corta: {len(GEMINI_API_KEY)} caracteres")
        else:
            logger.info(f"API key válida encontrada ({len(GEMINI_API_KEY)} caracteres)")

        headers = {
            "Content-Type": "application/json",
            'x-goog-api-key': GEMINI_API_KEY
        }
        
        # Crear prompt
        prompt = OcrTicketInput().build().system_prompt
        logger.info(f"Prompt generado: {prompt[:100]}...")
        
        # Verificar tamaño de la imagen
        image_size = len(image)
        logger.info(f"Tamaño de la imagen a enviar: {image_size} caracteres")
        
        # Verificar si la imagen es demasiado grande
        if image_size > 10485760:  # 10MB aprox
            logger.warning(f"La imagen es muy grande ({image_size} bytes), puede causar problemas")
            
        # Construir payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        },
                        {
                            "inline_data": {
                                "mime_type": 'image/jpeg',
                                "data": image,
                            },
                        },
                    ],
                },
            ],
            "generation_config": {
                "temperature": 0.2,
                "max_output_tokens": 4000,
            },
        }

        try:
            logger.info(f"Enviando solicitud a la API de Gemini: {self.url}")
            start_time = time.time()
            
            # Realizar la petición a Gemini
            response = requests.post(self.url, headers=headers, json=payload)
            
            # Medir tiempo de respuesta
            elapsed_time = time.time() - start_time
            logger.info(f"Respuesta recibida en {elapsed_time:.2f} segundos, código de estado: {response.status_code}")
            
            # Verificar si la respuesta es exitosa
            if response.status_code == 200:
                logger.info("Respuesta exitosa de la API de Gemini")
                return response.json()
            
            # Manejar errores específicos
            elif response.status_code == 400:
                error_detail = response.json()
                logger.error(f"Error 400 de Gemini API: {json.dumps(error_detail)}")
                raise Exception(f"Error de solicitud: {error_detail.get('error', {}).get('message', 'Desconocido')}")
            
            elif response.status_code == 401 or response.status_code == 403:
                logger.critical(f"Error de autenticación ({response.status_code}): API key inválida o no autorizada")
                raise Exception("API key inválida o no autorizada")
                
            elif response.status_code == 413:
                logger.error(f"Error 413: Entidad demasiado grande. Tamaño de la imagen: {image_size} caracteres")
                raise Exception("La imagen es demasiado grande para ser procesada por la API")
                
            else:
                # Para cualquier otro error
                try:
                    error_detail = response.json()
                    logger.error(f"Error {response.status_code} de Gemini API: {json.dumps(error_detail)}")
                except:
                    logger.error(f"Error {response.status_code} de Gemini API, respuesta no es JSON: {response.text[:200]}")
                
                raise Exception(f"Error en la API de Gemini: {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión: {str(e)}")
            raise Exception(f"Error de conexión con la API de Gemini: {str(e)}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout en la conexión: {str(e)}")
            raise Exception(f"Timeout en la conexión con la API de Gemini: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la petición HTTP: {str(e)}")
            raise Exception(f"Error en la petición a la API de Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Error inesperado al procesar la solicitud: {str(e)}")
