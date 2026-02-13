import os
import random
import logging
import psycopg2
from typing import Optional
from fastapi import FastAPI

# OpenTelemetry Imports
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

#OTLP Logging Provider
resource = Resource.create({"service.name": "fastapi-app"})
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

#configure the Exporter to point to Alloy
otlp_log_exporter = OTLPLogExporter(endpoint="http://alloy:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

#Trace Correlation Filter
class TraceIdFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            record.trace_id = format(span.get_span_context().trace_id, '032x')
            record.span_id = format(span.get_span_context().span_id, '16x')
        else:
            record.trace_id = '0' * 32
            record.span_id = '0' * 16
        return True

# standard Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [trace_id=%(trace_id)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.addFilter(TraceIdFilter())

# Attach OTLP Handler so logs go to Alloy
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logger.addHandler(handler)

app = FastAPI()
# 1. Instrument FastAPI (Starts the trace at the HTTP request)
FastAPIInstrumentor.instrument_app(app)
# 2. Instrument Psycopg2 (Adds the SQL execution to the same trace)
Psycopg2Instrumentor().instrument()

def get_db_connection():
    return psycopg2.connect(
        host="db",
        database=os.getenv("POSTGRES_DB", "demo"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

@app.get("/rolldice")
def roll_dice(roll: Optional[int] = None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if roll is not None:
        val = roll
        logger.info(f"Received forced roll from traffic script: {val}")
    else:
        val = random.randint(1, 6)
        logger.info(f"Generating random roll internally: {val}")
        
    cur.execute("INSERT INTO dice_history (roll_value) VALUES (%s) RETURNING id;", (val,))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"Dice roll {val} saved to database with ID {new_id}")
    
    return {"status": "success", "roll": val, "db_id": new_id}