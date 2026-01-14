from flask import Flask, request, jsonify
import sqlite3
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "licenses.db"

# ------------------ DB ------------------

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY,
        customer TEXT,
        machine_id TEXT UNIQUE,
        expire TEXT,
        status TEXT
    )
    """)
    con.commit()
    con.close()

init_db()

# ------------------ UTILS ------------------

def today():
    return datetime.utcnow().date()

# ------------------ API ------------------

@app.route("/activate", methods=["POST"])
def activate():
    data = request.json
    customer = data["customer"]
    machine = data["machine_id"]
    days = int(data.get("days", 7))

    expire = today() + timedelta(days=days)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("DELETE FROM licenses WHERE machine_id=?", (machine,))
    cur.execute("INSERT INTO licenses (customer, machine_id, expire, status) VALUES (?,?,?,?)",
                (customer, machine, expire.isoformat(), "ACTIVE"))
    con.commit()
    con.close()

    return jsonify({"status": "OK", "expire": expire.isoformat()})

@app.route("/check", methods=["POST"])
def check():
    machine = request.json["machine_id"]

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT expire, status FROM licenses WHERE machine_id=?", (machine,))
    row = cur.fetchone()
    con.close()

    if not row:
        return jsonify({"status": "NOT_FOUND"})

    expire, status = row
    if status != "ACTIVE":
        return jsonify({"status": "BLOCKED"})

    if today() > datetime.fromisoformat(expire).date():
        return jsonify({"status": "EXPIRED"})

    return jsonify({"status": "OK", "expire": expire})

@app.route("/admin")
def admin():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT customer, machine_id, expire, status FROM licenses")
    rows = cur.fetchall()
    con.close()

    html = "<h2>License Dashboard</h2><table border=1>"
    html += "<tr><th>Customer</th><th>Machine</th><th>Expire</th><th>Status</th></tr>"
    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"
    html += "</table>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
