from fastapi import FastAPI
import psycopg2
import os

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
    cur.execute("INSERT INTO dice_history (roll_value) VALUES (DEFAULT) RETURNING id;")
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Roll recorded!", "id": new_id}