# PagaMiPana OCR Backend - Python

Backend OCR para extracción de información de tickets usando Google Gemini Vision API.

## 🚀 Inicio Rápido

### Desarrollo Local

1. **Crear entorno virtual e instalar dependencias:**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configurar variable de entorno:**
```bash
export GEMINI_API_KEY=tu_api_key_aqui
```

3. **Iniciar servidor:**
```bash
python main.py
```

El servidor estará disponible en `http://localhost:8080`

### Endpoints Disponibles

- **GET** `/health` - Health check
- **POST** `/api/ocr` - OCR desde archivo multipart (desarrollo local)
- **POST** `/api/ocr/base64` - OCR desde JSON con base64 (Lambda/producción)

### Ejemplos de Uso

**Health Check:**
```bash
curl http://localhost:8080/health
```

**OCR desde archivo (local):**
```bash
curl -X POST http://localhost:8080/api/ocr \
  -F "file=@imagen.jpg"
```

**OCR desde base64 (Lambda):**
```bash
curl -X POST http://localhost:8080/api/ocr/base64 \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_string_aqui"}'
```

## 🐳 Despliegue en AWS Lambda

### 1. Construir imagen Docker

```bash
./build_python.sh
```

### 2. Subir a Amazon ECR

```bash
# Autenticarse
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Etiquetar
docker tag pagamipana-ocr-lambda-python:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/pagamipana-ocr-lambda-python:latest

# Subir
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/pagamipana-ocr-lambda-python:latest
```

### 3. Crear función Lambda

1. Ve al AWS Console > Lambda
2. Create function > Container image
3. Function name: `pagamipana-ocr-python`
4. Container image URI: URI de ECR
5. Configurar:
   - Environment variables: `GEMINI_API_KEY`
   - Timeout: 60 segundos
   - Memory: 512 MB
6. Crear Function URL con CORS habilitado

## 📝 Estructura del Proyecto

```
.
├── main.py                      # Servidor FastAPI principal
├── requirements.txt             # Dependencias Python
├── Dockerfile.lambda.python     # Dockerfile para Lambda
├── build_python.sh              # Script de build
└── README_PYTHON.md            # Este archivo
```

## 🔧 Tecnologías

- **FastAPI** - Framework web
- **Google Generative AI** - SDK oficial de Gemini
- **Mangum** - Adaptador ASGI para AWS Lambda
- **Uvicorn** - Servidor ASGI
