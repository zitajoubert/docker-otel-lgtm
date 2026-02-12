# Use Python 3.10+ as requested
FROM python:3.10-slim

WORKDIR /app

# Install dependencies for FastAPI and Postgres 
RUN pip install requirements.txt
# Install the auto-instrumentation components 
RUN opentelemetry-bootstrap -a install

COPY . .

# Use the wrapper to start the app without manual code changes [
ENTRYPOINT ["opentelemetry-instrument"]
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]