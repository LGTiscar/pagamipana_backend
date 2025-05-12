import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.infrastructure.rest.server.ocr_rest:app", host="0.0.0.0", port=8000, reload=True)