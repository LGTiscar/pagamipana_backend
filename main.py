import os
import io
import base64
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
from PIL import Image
from mangum import Mangum
import jwt
from jwt import PyJWKClient

app = FastAPI(title="PagaMiPana OCR Backend")

# CORS - sin credentials para wildcard origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# Autenticación: exigir un JWT válido de Supabase en las peticiones de OCR.
# El frontend envía `Authorization: Bearer <access_token>`. Esto evita que el
# endpoint sea abierto (abuso de coste / OCR gratis).
#   - HS256: verifica con SUPABASE_JWT_SECRET (secreto JWT clásico).
#   - ES256/RS256: verifica contra el JWKS del proyecto (claves asimétricas).
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
_jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json") if SUPABASE_URL else None


async def require_user(request: Request) -> dict:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de autenticación")
    token = auth.split(" ", 1)[1].strip()
    try:
        alg = jwt.get_unverified_header(token).get("alg")
        if alg == "HS256":
            if not SUPABASE_JWT_SECRET:
                raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET no configurado")
            return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        if _jwks_client is None:
            raise HTTPException(status_code=500, detail="SUPABASE_URL no configurado")
        key = _jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=[alg], audience="authenticated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


class ImageRequest(BaseModel):
    image: str  # base64 encoded image


class HealthResponse(BaseModel):
    status: str
    service: str


class OcrResult(BaseModel):
    success: bool
    text: str
    structured_data: Optional[dict] = None


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        service="pagamipana-ocr-backend-python"
    )


@app.post("/api/ocr", response_model=OcrResult)
async def ocr_from_file(file: UploadFile = File(...), user: dict = Depends(require_user)):
    """OCR endpoint que acepta multipart/form-data (para desarrollo local)"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    # Leer imagen
    image_bytes = await file.read()

    return await process_image(image_bytes)


@app.post("/api/ocr/base64", response_model=OcrResult)
async def ocr_from_base64(request: ImageRequest, user: dict = Depends(require_user)):
    """OCR endpoint que acepta JSON con base64 (para Lambda/producción)"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    # Decodificar base64
    try:
        # Remover prefijo data:image si existe
        base64_str = request.image
        if "base64," in base64_str:
            base64_str = base64_str.split("base64,")[1]

        image_bytes = base64.b64decode(base64_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")

    return await process_image(image_bytes)


# Optimización de imagen (A1): los tickets son largos y estrechos;
# 1568px de lado largo conserva la legibilidad del texto pequeño.
MAX_IMAGE_DIMENSION = 1568
JPEG_QUALITY = 80


def optimize_image(image_bytes: bytes) -> bytes:
    """Redimensiona y recomprime la imagen para reducir los tiles que procesa Gemini."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # JPEG no soporta alpha ni modos no-RGB
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Redimensionar in-place manteniendo aspecto solo si excede el máximo
    img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue()


# Config de generación (A2): JSON directo evita limpiar fences markdown y
# reduce fallos de parseo; temperature 0 y tope de tokens recortan latencia.
GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "temperature": 0,
    "max_output_tokens": 2048,
}


async def process_image(image_bytes: bytes) -> OcrResult:
    """Procesa la imagen con Gemini Vision"""
    try:
        # A1: reducir tamaño/peso antes de enviar a Gemini
        image_bytes = optimize_image(image_bytes)

        # Configurar el modelo
        model = genai.GenerativeModel(
            'gemini-3.1-flash-lite',
            generation_config=GENERATION_CONFIG,
        )

        # Prompt para extracción estructurada
        prompt = """
You are an OCR and information extraction model specialized in retail and restaurant receipts.

TASK:
Analyze the provided image of a receipt and extract ONLY the following information:
- Each purchased product (one entry per line item)
- The quantity of each product
- The TOTAL price for that product line (unit price × quantity)
- The GRAND TOTAL of the receipt

IGNORE completely:
- Business name, address, tax ID
- Date, time, table number, waiter, payment method
- Taxes, VAT breakdowns, base amounts, discounts
- Any text not related to purchased items or the final total

IMPORTANT RULES:
1. Only include actual purchased items (food, drinks, etc.).
2. Quantity must be numeric. If quantity is not explicitly shown, infer it from the receipt format when clearly possible.
3. priceTotal must always be the TOTAL for that line, not the unit price.
4. Do not invent items or values that are not visible in the receipt.
5. Do not return explanations, comments, or confidence notes.
6. Output MUST be valid JSON and MUST strictly follow the schema below.
7. Do not include any extra fields beyond those defined in the schema.

OUTPUT FORMAT:
Return a single JSON object with this structure:
{
  "items": [
    {
      "description": "Product name",
      "quantity": 1.0,
      "priceTotal": 10.50
    }
  ],
  "total": 100.50
}

- Use decimal numbers with a dot (.) as separator.
- Preserve original product naming language from the receipt.
- If the receipt shows a final total (e.g., TOTAL, TOTAL A PAGAR), extract it as "total".
- If multiple totals appear, choose the final amount paid.

Now process the receipt image and return ONLY the JSON result, no other text.
"""

        # Preparar la imagen
        image_data = {
            'mime_type': 'image/jpeg',  # Gemini auto-detecta el tipo real
            'data': image_bytes
        }

        # Generar contenido
        response = model.generate_content([prompt, image_data])

        # Extraer texto
        result_text = response.text.strip()

        # A2: con response_mime_type=application/json Gemini devuelve JSON
        # directo, sin fences markdown que limpiar.
        import json
        try:
            structured_data = json.loads(result_text)
        except json.JSONDecodeError:
            # Si no es JSON válido, devolver como texto plano
            structured_data = None

        return OcrResult(
            success=True,
            text=result_text,
            structured_data=structured_data
        )

    except HTTPException:
        # Errores de validación (p. ej. imagen inválida) deben propagarse tal cual
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")


# Handler para AWS Lambda
lambda_handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
