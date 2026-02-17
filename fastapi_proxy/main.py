import os
import requests
import logging
import uvicorn
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name__)

url = os.getenv("url", "http//app:8000/rolldice")
app = FastApi()

@app.get("/caller")
def caller():
    logger.info(f"Forwaring request to: {url}")
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        logger.exception("Failed to connect to API")
        return {error: str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_config=None)

