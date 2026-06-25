# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

PagaMiPana OCR backend: a single-file FastAPI service that extracts line items and totals from retail/restaurant receipt images using Google Gemini Vision. It runs both as a local server (Uvicorn) and as an AWS Lambda container (via Mangum). All application logic lives in `main.py`.

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run locally (serves on http://localhost:8080, override with PORT)
export GEMINI_API_KEY=...   # required, or /api/ocr endpoints return 500
python main.py

# Build the Lambda container image locally
./build_python.sh           # docker build -f Dockerfile.lambda.python
```

There is no test suite, linter, or formatter configured. Verify changes manually with the endpoints below (e.g. `curl http://localhost:8080/health`).

## Architecture

- **Dual runtime, one app.** The same `FastAPI` instance serves local HTTP (the `__main__` block runs Uvicorn) and Lambda (`lambda_handler = Mangum(app, lifespan="off")`, the container `CMD`). Keep both paths working when changing startup behavior.
- **Two OCR entrypoints, one core.** `/api/ocr` accepts `multipart/form-data` (local/dev convenience); `/api/ocr/base64` accepts JSON with a base64 string (used in production behind the Lambda Function URL, where binary uploads are awkward). Both decode to bytes and call the shared `process_image()`. Add new input formats by funneling into `process_image`, not by duplicating Gemini logic.
- **Gemini model + prompt are the product.** `process_image()` calls a hardcoded Gemini model (`gemini-2.5-flash-lite`) with a long English extraction prompt that defines the exact output schema (`items[]` with `description`/`quantity`/`priceTotal`, plus `total`). Changing the model name or prompt directly changes extraction behavior — the model name has been deliberately tuned across commits.
- **Response shape.** Returns `OcrResult { success, text, structured_data }`. `text` is Gemini's raw response (markdown code fences stripped); `structured_data` is the parsed JSON, or `None` if parsing fails (the service does not error on unparseable model output — it falls back to returning raw text).
- **CORS is fully open** (`allow_origins=["*"]`, `allow_credentials=False`) because the frontend calls the Lambda Function URL directly from the browser.

## Deployment

Push to `master` triggers `.github/workflows/deploy.yml`: builds the image with `docker buildx --platform linux/amd64`, pushes to ECR (`pagamipana-ocr-lambda-python` in `eu-north-1`), and runs `aws lambda update-function-code` on the `pagamipana-ocr-python` function. Requires `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` repo secrets. `GEMINI_API_KEY` is set as a Lambda environment variable, not in the repo.
