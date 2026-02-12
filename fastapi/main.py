from fastapi import FastAPI
import psycopg2
import os
import random

app = FastAPI()

def get_db_connection():
    return psycopg2.connect(
        host="db", # Matches the service name in docker-compose
        database=os.getenv("POSTGRES_DB", "demo"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

@app.get("/rolldice")
def roll_dice():
    conn = get_db_connection()
    cur = conn.cursor()
    val = random.randint(1, 6)
    cur.execute("INSERT INTO dice_history (roll_value) VALUES (%s) RETURNING id;", (val,))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "roll": val, "db_id": new_id}