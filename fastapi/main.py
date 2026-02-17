import os
import random
import logging
import psycopg2
from typing import Optional
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor


from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

# 1. Define Common Resource (Used for both Logs and Traces)                                             #Trace filtering en trace logging vanaf gemini
resource = Resource.create({"service.name": "fastapi-app"})

# 2. Initialize TRACING 
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
# Sends traces to Alloy on port 4317
otlp_trace_exporter = OTLPSpanExporter(endpoint="http://alloy:4317", insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))

# 3. Initialize LOGGING
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
otlp_log_exporter = OTLPLogExporter(endpoint="http://alloy:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

# Trace Correlation Filter for local stdout logs
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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [trace_id=%(trace_id)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.addFilter(TraceIdFilter())

# Attach OTLP Handler so logs go to Alloy/Loki
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logger.addHandler(handler)


app = FastAPI()

@app.exception_handler(Exception)                                                       #gekry by gemini - hanteer die DB loki errors 
async def global_exception_handler(request: Request, exc: Exception):
    # This captures the full stack trace and sends it to Loki via OTLP
    logger.exception("Unhandled Internal Server Error: %s", exc)
    
    # Ensure the log is flushed to Alloy before the response is sent
    logger_provider.force_flush()
    
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"},
    )

# Auto-instruments HTTP requests (starts the trace)
FastAPIInstrumentor.instrument_app(app)
# Auto-instruments Postgres queries (adds SQL as a child span)
Psycopg2Instrumentor().instrument()



def get_db_connection():                                    # my api code
    return psycopg2.connect(            
        host="db",
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        connect_timeout=5  
    )

@app.get("/rolldice")
def roll_dice(roll: Optional[int] = None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        val = roll if roll is not None else random.randint(1, 6)
        logger.info(f"Processing dice roll: {val}")
    
        cur.execute("INSERT INTO dice_history (roll_value) VALUES (%s) RETURNING id;", (val,))
        new_id = cur.fetchone()[0]
        conn.commit()
        
        cur.close()
        logger.info(f"Dice roll {val} saved to database with ID {new_id}")
        return {"status": "success", "roll": val, "db_id": new_id}

    except Exception as e:
        logger.exception("Failed to process dice roll")
        raise HTTPException(status_code=500, detail="Database error")
    
    finally:
        if conn:
            conn.close()