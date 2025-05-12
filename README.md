# Pagamipana Backend

A FastAPI backend service that uses Google's Gemini API to perform OCR analysis on restaurant receipts, extracting menu items, quantities, prices, and total bill amount.

## Overview

This project follows a clean architecture approach with distinct layers:

- **Application**: Contains use cases that orchestrate the business logic
- **Domain**: Core business logic, models, services, and interfaces
- **Infrastructure**: Technical implementations, REST API, DTOs, and external services

## Features

- OCR analysis of restaurant receipts using Google Gemini API
- JSON response with structured receipt information
- Clean architecture approach for maintainability and testability

## Requirements

- Python 3.11
- Dependencies listed in `requirements.txt`
- Google Gemini API key

## Installation

1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Running the Application

Start the development server:

```bash
python run.py
```

The server will be available at http://0.0.0.0:8000

## API Endpoints

### Health Check
```
GET /
```
Returns a simple message confirming the service is running.

Response:
```json
{
  "message": "Gemini API Proxy Service"
}
```

### OCR Analysis
```
POST /api/ocr/generate
```
Analyzes a receipt image and returns structured data.

**Request Body**:
```json
{
  "image": "base64_encoded_image_string"
}
```

**Response**:
```json
{
  "items": [
    {"name": "Item Name 1", "quantity": 2, "unitPrice": 10.99, "totalPrice": 21.98},
    {"name": "Item Name 2", "quantity": 1, "unitPrice": 5.99, "totalPrice": 5.99}
  ],
  "total": 27.97
}
```

**Error Handling**:
- 400 Bad Request: Returned if the image is missing or invalid
- 500 Internal Server Error: Returned if the API key is not found or other server issues occur

## Deployment

The project includes a `vercel.json` configuration for deploying to Vercel.

## Project Structure

- `app` - Main application code
  - `application/` - Use cases
  - `domain/` - Business logic, models and interfaces
  - `infrastructure/` - Technical implementations
    - `dto/` - Data Transfer Objects
    - `llm/` - Language Model configurations
    - `rest/` - REST API endpoints and clients

## License

This project is proprietary and confidential.