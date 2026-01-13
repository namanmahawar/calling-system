from flask import Flask, render_template, request, redirect, flash, session
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
        balance REAL DEFAULT 0,
        remarks TEXT,
        commit_date TEXT,
        call_done INTEGER DEFAULT 0
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
        flash("Invalid username or password")

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
            flash("Account created. Please login.")
            return redirect("/")
        except:
            flash("Username already exists")
        finally:
            conn.close()

    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    logout_user()
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
        "SELECT company_name FROM companies WHERE id=? AND user_id=?",
        (cid, current_user.id)
    ).fetchone()

    data = c.execute(
        "SELECT * FROM debtors WHERE company_id=?",
        (cid,)
    ).fetchall()

    conn.close()

    if not company:
        return redirect("/companies")

    return render_template(
        "dashboard.html",
        company_name=company[0],
        data=data
    )

# ---------------- UPLOADS ----------------
@app.route("/upload/balance", methods=["POST"])
@login_required
def upload_balance():
    cid = session.get("company_id")
    df = pd.read_excel(request.files["file"])

    conn = get_db()
    c = conn.cursor()

    for _, r in df.iterrows():
        c.execute(
            "INSERT INTO debtors(company_id, party, balance) VALUES (?,?,?)",
            (cid, str(r[0]).strip(), float(r[1]))
        )

    conn.commit()
    conn.close()
    flash("Balance uploaded")
    return redirect("/dashboard")

@app.route("/upload/contacts", methods=["POST"])
@login_required
def upload_contacts():
    cid = session.get("company_id")
    df = pd.read_excel(request.files["file"])

    conn = get_db()
    c = conn.cursor()

    for _, r in df.iterrows():
        mobile = str(r[1]).strip()
        c.execute(
            "UPDATE debtors SET mobile=?, whatsapp=? WHERE company_id=? AND party=?",
            (mobile, mobile, cid, str(r[0]).strip())
        )

    conn.commit()
    conn.close()
    flash("Contacts uploaded")
    return redirect("/dashboard")

# ---------------- INIT ----------------
init_db()

if __name__ == "__main__":
    app.run(debug=True)
