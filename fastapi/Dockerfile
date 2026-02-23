# Use Python 3.10+ as requested
FROM python:3.10-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap -a install
COPY . .
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://alloy.monitoring.svc:4318"
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_SERVICE_NAME="dice-server"
ENTRYPOINT ["opentelemetry-instrument"]
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]