import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "appdb"),
        user=os.getenv("POSTGRES_USER", "appuser"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        connect_timeout=3,
    )

@app.route("/health")
def health():
    return jsonify(status="ok")

@app.route("/api/visits")
def visits():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY, ts TIMESTAMP DEFAULT now())")
    cur.execute("INSERT INTO visits DEFAULT VALUES")
    cur.execute("SELECT count(*) FROM visits")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(visits=count, version=os.getenv("APP_VERSION", "dev"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
