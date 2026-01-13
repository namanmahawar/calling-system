from flask import Flask, render_template, request, redirect, flash, session, jsonify
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, UserMixin, current_user
)
import sqlite3
import os
import pandas as pd

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager(app)
login_manager.login_view = "/"

DB_PATH = "data/db.sqlite"

# ---------------- DATABASE ----------------
def get_db():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS debtors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        party TEXT,
        mobile TEXT,
        whatsapp TEXT,
        balance REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

# ---------------- USER ----------------
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    c = conn.cursor()
    row = c.execute(
        "SELECT id, username FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    return User(row[0], row[1]) if row else None

# ---------------- AUTH ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        row = c.execute(
            "SELECT id, username FROM users WHERE username=? AND password=?",
            (u, p)
        ).fetchone()
        conn.close()

        if row:
            login_user(User(row[0], row[1]))
            return redirect("/companies")

        flash("Invalid login")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users(username,password) VALUES (?,?)",
                (u, p)
            )
            conn.commit()
            flash("Account created. Login now.")
            return redirect("/")
        except:
            flash("Username already exists")
        finally:
            conn.close()

    return render_template("signup.html")

@app.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect("/")

# ---------------- COMPANIES ----------------
@app.route("/companies", methods=["GET", "POST"])
@login_required
def companies():
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["company_name"]
        c.execute(
            "INSERT INTO companies(user_id, company_name) VALUES (?,?)",
            (current_user.id, name)
        )
        conn.commit()

    rows = c.execute(
        "SELECT id, company_name FROM companies WHERE user_id=?",
        (current_user.id,)
    ).fetchall()
    conn.close()

    return render_template("company_list.html", companies=rows)

@app.route("/set-company/<int:cid>")
@login_required
def set_company(cid):
    session["company_id"] = cid
    return redirect("/dashboard")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    cid = session.get("company_id")
    if not cid:
        return redirect("/companies")

    conn = get_db()
    c = conn.cursor()

    company = c.execute(
        "SELECT company_name FROM companies WHERE id=?",
        (cid,)
    ).fetchone()

    data = c.execute(
        "SELECT * FROM debtors WHERE company_id=?",
        (cid,)
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        company_name=company[0],
        data=data
    )

# ---------------- UPLOAD BALANCE ----------------
@app.route("/upload/balance", methods=["POST"])
@login_required
def upload_balance():
    try:
        cid = session.get("company_id")
        df = pd.read_excel(request.files["file"], dtype=str)

        conn = get_db()
        c = conn.cursor()

        for _, r in df.iterrows():
            party = str(r.iloc[0]).strip()
            balance = float(str(r.iloc[1]).replace(",", "").strip())

            c.execute("""
                INSERT INTO debtors(company_id, party, balance)
                VALUES (?,?,?)
            """, (cid, party, balance))

        conn.commit()
        conn.close()
        flash("Balance uploaded successfully")

    except Exception as e:
        flash(f"Balance upload error: {e}")

    return redirect("/dashboard")

# ---------------- UPLOAD CONTACTS (FIXED .0 ISSUE) ----------------
@app.route("/upload/contacts", methods=["POST"])
@login_required
def upload_contacts():
    try:
        cid = session.get("company_id")

        # dtype=str is MOST IMPORTANT
        df = pd.read_excel(request.files["file"], dtype=str)

        conn = get_db()
        c = conn.cursor()

        for _, r in df.iterrows():
            party = str(r.iloc[0]).strip()
            mobile = str(r.iloc[1]).strip()

            # Excel .0 FIX
            if mobile.endswith(".0"):
                mobile = mobile[:-2]

            c.execute("""
                UPDATE debtors
                SET mobile=?, whatsapp=?
                WHERE company_id=? AND party=?
            """, (mobile, mobile, cid, party))

        conn.commit()
        conn.close()
        flash("Contacts uploaded successfully")

    except Exception as e:
        flash(f"Contact upload error: {e}")

    return redirect("/dashboard")

# ---------------- UPDATE NUMBER FROM WEBSITE ----------------
@app.route("/update-number", methods=["POST"])
@login_required
def update_number():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE debtors SET mobile=?, whatsapp=? WHERE id=?",
        (data["number"], data["number"], data["id"])
    )
    conn.commit()
    conn.close()
    return jsonify(success=True)

# ---------------- INIT ----------------
init_db()

if __name__ == "__main__":
    app.run(debug=True)
