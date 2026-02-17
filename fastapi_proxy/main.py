import requests
from opentelemetry.instrumentation.requests import RequestsInstrumentor

RequestsInstrumentor().instrument()

@app.get("/caller")
def caller():
    response = requests.get("http://localhost:8000/rolldice")
    print("Connected to rolldice api")
    return response.json()