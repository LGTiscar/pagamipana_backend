from dotenv import load_dotenv
from app.domain.interfaces.OcrClient import OcrClient
import os
import logging
import traceback
import json
import time
import io
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

from app.domain.models.Exceptions.ApiKeyNotFoundException import ApiKeyNotFoundException
from app.infrastructure.llm.OcrTicketInput import OcrTicketInput

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logger = logging.getLogger(__name__)

class GeminiClient(OcrClient):
    def __init__(self, model_name: str = 'gemini-2.0-flash-lite'): 
        if not GEMINI_API_KEY:
            logger.critical("API key de Gemini no encontrada en variables de entorno.")
            raise ApiKeyNotFoundException("API key de Gemini no encontrada en variables de entorno")

        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("Gemini Client inicializado.")
        except Exception as e:
            logger.critical(f"Error configurando o inicializando el cliente de Gemini: {e}")
            raise Exception(f"Error al inicializar el cliente de Gemini: {str(e)}")

        self.model_name_for_library = model_name

    def get_analysis(self, image_bytes: bytes, image_mime_type: str) -> dict:
        logger.info(f"Iniciando análisis con Gemini, modelo {self.model_name_for_library}")
        logger.info(f"Tipo de imagen: {image_mime_type}")

        prompt_text = OcrTicketInput().build().system_prompt

        image_size_bytes = len(image_bytes)
        logger.info(f"Tamaño de la imagen a enviar: {image_size_bytes} bytes")

        if image_size_bytes > 20 * 1024 * 1024: # 20MB
            logger.warning(f"La imagen ({image_size_bytes} bytes) supera los 20MB, puede ser rechazada.")


        uploaded_file_resource = None
        json_response_text = ""

        try:
            logger.info("Subiendo imagen...")
            
            # Wrap image_bytes in io.BytesIO as per library requirements
            image_file_stream = io.BytesIO(image_bytes)

            # Prepare config dictionary for mime_type and display_name
            upload_config = {
                "mime_type": image_mime_type,
                "display_name": f"ticket-{time.time()}",
            }

            uploaded_file_resource = self.client.files.upload(
                file=image_file_stream, 
                config=upload_config
            )
            
            uploaded_file_name = getattr(uploaded_file_resource, 'name', None)
            if not uploaded_file_name:
                logger.warning("No se pudo obtener 'name' del recurso de archivo subido. Intentando 'uri'.")
                uploaded_file_name = getattr(uploaded_file_resource, 'uri', None)
         
            logger.info(f"URI del archivo subido: {uploaded_file_resource.uri}")
            
            # Explicitly construct a single Content object containing all parts
            # for the current turn.
            current_turn_content = types.Content(
                parts=[
                    types.Part.from_text(text=prompt_text),
                    types.Part.from_uri(
                        file_uri=uploaded_file_resource.uri, 
                        mime_type=image_mime_type
                    )
                ],
                role="user"  # Specify the role for the content
            )

            response = self.client.models.generate_content(
                model=self.model_name_for_library,
                contents=[current_turn_content],  # Pass a list containing the single Content object
            )

            logger.info(f"Resultado de la solicitud de análisis de Gemini (genai.Client): {response}")

            try:
                if response.candidates and \
                   response.candidates[0].content and \
                   response.candidates[0].content.parts and \
                   response.candidates[0].content.parts[0].text:
                    json_response_text = response.candidates[0].content.parts[0].text
                    if json_response_text.startswith("```json"):
                        json_response_text = json_response_text[7:]
                    if json_response_text.endswith("```"):
                        json_response_text = json_response_text[:-3]
                    json_response_text = json_response_text.strip()
                else:
                    logger.error("Respuesta de Gemini no contiene la estructura esperada para el texto. Respuesta: %s", response)
                    raise Exception("Respuesta de Gemini inválida: no contiene datos de texto en la estructura esperada.")
            except AttributeError as e:
                logger.error(f"Error accediendo a partes de la respuesta de Gemini: {e}. Respuesta: {response}")
                raise Exception(f"Respuesta de Gemini inválida o estructura inesperada: {e}")

            logger.info("Respuesta de texto JSON de Gemini (genai.Client) recibida.")
            
            analysis_result = json.loads(json_response_text)
            logger.info("Análisis de Gemini (genai.Client) procesado exitosamente.")
            return analysis_result

        except google_exceptions.InvalidArgument as e:
            logger.error(f"Error de solicitud inválida (400) con Gemini API (genai.Client): {e.message if hasattr(e, 'message') else e}")
            raise Exception(f"Error de solicitud inválida a Gemini: {e.message if hasattr(e, 'message') else e}")
        except google_exceptions.PermissionDenied as e:
            logger.critical(f"Error de autenticación/permiso (401/403) con Gemini API (genai.Client): {e.message if hasattr(e, 'message') else e}")
            raise ApiKeyNotFoundException(f"API key inválida o no autorizada para Gemini: {e.message if hasattr(e, 'message') else e}")
        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Recurso agotado con Gemini API (genai.Client): {e.message if hasattr(e, 'message') else e}")
            raise Exception(f"Límite de API de Gemini alcanzado o el archivo es demasiado grande: {e.message if hasattr(e, 'message') else e}")
        except google_exceptions.DeadlineExceeded as e:
            logger.error(f"Timeout en la conexión con Gemini API (genai.Client): {e.message if hasattr(e, 'message') else e}")
            raise Exception(f"Timeout en la conexión con la API de Gemini: {e.message if hasattr(e, 'message') else e}")
        except google_exceptions.FailedPrecondition as e:
            logger.error(f"Error de precondición fallida con Gemini API (genai.Client): {e.message if hasattr(e, 'message') else e}")
            raise Exception(f"Problema con el archivo procesado por Gemini: {e.message if hasattr(e, 'message') else e}")
        except google_exceptions.GoogleAPIError as e: # Catch-all for other Google API errors
            logger.error(f"Error genérico en la API de Gemini (genai.Client): Código {e.code if hasattr(e, 'code') else 'N/A'} - {e.message if hasattr(e, 'message') else e}")
            raise Exception(f"Error en la API de Gemini (genai.Client): {e.message if hasattr(e, 'message') else e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON de la respuesta de Gemini: {e}. Respuesta parcial: {json_response_text[:200]}...")
            raise Exception(f"Error procesando la respuesta de Gemini (JSON inválido): {e}")
        except Exception as e: # Catch other unexpected errors, including potential AttributeError if client methods are different
            logger.error(f"Error inesperado durante el análisis con Gemini (genai.Client): {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Error inesperado al procesar la solicitud con Gemini: {str(e)}")
