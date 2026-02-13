from fastapi import FastAPI
import psycopg2
import os
import random
import logging
from typing import Optional
from opentelemetry import trace

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

logger.addFilter(TraceIdFilter())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

def get_db_connection():
    return psycopg2.connect(
        host="db", # Matches the service name in docker-compose
        database=os.getenv("POSTGRES_DB", "demo"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

@app.get("/rolldice")
def roll_dice(roll: Optional[int] = None):
    conn = get_db_connection()
    cur = conn.cursor()
    # 1. Check if the script sent a specific number
    if roll is not None:
        val = roll
        logger.info(f"Received forced roll from traffic script: {val}")
    else:
        # 2. If no number sent, generate one (fallback)
        val = random.randint(1, 6)
        logger.info(f"Generating random roll internally: {val}")
    cur.execute("INSERT INTO dice_history (roll_value) VALUES (%s) RETURNING id;", (val,))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"Dice roll {val} saved to database with ID {new_id}")
    
    return {"status": "success", "roll": val, "db_id": new_id}

