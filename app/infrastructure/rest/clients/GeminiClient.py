from dotenv import load_dotenv
from app.domain.interfaces.OcrClient import OcrClient
import os
import requests

from app.domain.models.Exceptions.ApiKeyNotFoundException import ApiKeyNotFoundException
from app.infrastructure.llm.OcrTicketInput import OcrTicketInput

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiClient(OcrClient):
    def __init__(self, model: str = 'gemini-2.0-flash'):
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def get_analysis(self, image: str) -> dict:
        if not GEMINI_API_KEY:
            raise ApiKeyNotFoundException

        headers = {
            "Content-Type": "application/json",
            'x-goog-api-key': GEMINI_API_KEY
        }
        prompt = OcrTicketInput().build().system_prompt
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
            response = requests.post(self.url, headers=headers, json=payload)
            return response.json()
        except Exception as e :
            raise Exception(f"Error: {e}")
