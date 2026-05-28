from flask import Flask, request, redirect, render_template
import sqlite3
import random
import string
import qrcode
import os

app = Flask(__name__)

# ---------------- DATABASE SETUP ---------------- #

def init_db():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            long_url TEXT NOT NULL,

            short_code TEXT NOT NULL UNIQUE,

            clicks INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- GENERATE SHORT CODE ---------------- #

def generate_short_code(length=6):

    characters = string.ascii_letters + string.digits

    while True:

        short_code = ''.join(
            random.choice(characters)
            for _ in range(length)
        )

        conn = sqlite3.connect("database.db")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM urls WHERE short_code=?",
            (short_code,)
        )

        existing = cursor.fetchone()

        conn.close()

        if not existing:
            return short_code

# ---------------- HOME PAGE ---------------- #

@app.route("/", methods=["GET", "POST"])
def home():

    short_url = None
    qr_path = None
    clicks = 0

    if request.method == "POST":

        long_url = request.form["long_url"]

        short_code = generate_short_code()

        conn = sqlite3.connect("database.db")

        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO urls (long_url, short_code) VALUES (?, ?)",
            (long_url, short_code)
        )

        conn.commit()
        conn.close()

        # CREATE SHORT URL

        short_url = request.host_url + short_code

        # CREATE QR CODE

        os.makedirs("static/qr_codes", exist_ok=True)

        qr = qrcode.make(short_url)

        qr_path = f"static/qr_codes/{short_code}.png"

        qr.save(qr_path)

        # GET CLICKS

        conn = sqlite3.connect("database.db")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT clicks FROM urls WHERE short_code=?",
            (short_code,)
        )

        result = cursor.fetchone()

        if result:
            clicks = result[0]

        conn.close()

    return render_template(
        "index.html",
        short_url=short_url,
        qr_code=qr_path,
        clicks=clicks
    )

# ---------------- REDIRECT ROUTE ---------------- #

@app.route("/<short_code>")
def redirect_to_url(short_code):

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT long_url FROM urls WHERE short_code=?",
        (short_code,)
    )

    result = cursor.fetchone()

    if result:

        # UPDATE CLICK COUNT

        cursor.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE short_code=?",
            (short_code,)
        )

        conn.commit()

        conn.close()

        return redirect(result[0])

    conn.close()

    return "URL not found"

# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":
    app.run(debug=True)