# Use Python 3.10+ as requested [cite: 7]
FROM python:3.10-slim

WORKDIR /app

# Install dependencies for FastAPI and Postgres [cite: 7, 8]
RUN pip install fastapi uvicorn psycopg2-binary \
    opentelemetry-distro \
    opentelemetry-exporter-otlp

# Install the auto-instrumentation components [cite: 12]
RUN opentelemetry-bootstrap -a install

COPY . .

# Use the wrapper to start the app without manual code changes [cite: 21, 22]
ENTRYPOINT ["opentelemetry-instrument"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]