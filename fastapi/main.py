import os
import random
import logging
import psycopg2
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Standard Python Logging - No OTLP or Trace Filtering code needed here!
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('__name__')

app = FastAPI()

# Your global exception handler remains, but logger.exception will now be caught 
# and correlated by the auto-instrumentation agent.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled Internal Server Error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"},
    )

def get_db_connection():
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
        logger.info(f"Processing dice roll: {val}") # Agent captures this
    
        cur.execute("INSERT INTO dice_history (roll_value) VALUES (%s) RETURNING id;", (val,))
        new_id = cur.fetchone()[0]
        conn.commit()
        
        cur.close()
        logger.info(f"Dice roll {val} saved to database with ID {new_id}")
        return {"status": "success", "roll": val, "db_id": new_id}

    except Exception as e:
        logger.exception("Failed to process dice roll")
        return JSONResponse(status_code=500, content={"message": "Database error"})
    
    finally:
        if conn:
            conn.close()

