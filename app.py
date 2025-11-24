import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import connect, Error
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_PRIVATE_IP')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME', 'cloudcontacts')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change_me')

def get_conn():
    try:
        return connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            autocommit=True,
        )
    except Error as e:
        app.logger.error(f"DB Error: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()

        if not name or not email:
            flash("Name and email are required", "error")
            return redirect(url_for("index"))

        conn = get_conn()
        if conn is None:
            flash("Cannot connect to database", "error")
            return redirect(url_for("index"))

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO contacts (name, email, phone, created_at) VALUES (%s, %s, %s, %s)",
                    (name, email, phone, datetime.utcnow())
                )
            flash("Contact saved successfully", "success")
        except Error as e:
            if "Duplicate" in str(e):
                flash("Email already exists", "error")
            else:
                flash("Database error", "error")
        finally:
            conn.close()

        return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/contacts")
def contacts():
    conn = get_conn()
    if conn is None:
        flash("Cannot connect to database", "error")
        return render_template("contacts.html", contacts=[])

    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT id, name, email, phone, created_at FROM contacts ORDER BY created_at DESC")
            data = cur.fetchall()
        return render_template("contacts.html", contacts=data)
    except:
        flash("Error loading contacts", "error")
        return render_template("contacts.html", contacts=[])
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
