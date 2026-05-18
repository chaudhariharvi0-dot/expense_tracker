import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import requests

# -------- LOAD ENV -------- #
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
DB_NAME = os.getenv("DATABASE_NAME", "spendwise.db")

# Currency Conversion Rates (Free API)
EXCHANGE_RATES_URL = "https://api.exchangerate-api.com/v4/latest"

def get_exchange_rate(from_currency, to_currency):
    """Get exchange rate between two currencies"""
    try:
        response = requests.get(f"{EXCHANGE_RATES_URL}/{from_currency}")
        data = response.json()
        return data['rates'].get(to_currency, 1)
    except:
        return 1  # Default to 1 if API fails

# -------- DATABASE -------- #

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        preferred_currency TEXT DEFAULT 'INR',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT CHECK(type IN ('income','expense')) NOT NULL,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        amount_in_base REAL NOT NULL,
        category TEXT NOT NULL,
        note TEXT,
        date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Custom Categories Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        icon TEXT,
        color TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, category_name),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'INR',
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()


init_db()

# =====================================================
# ----------- DEFAULT CATEGORIES ----------------------
# =====================================================

DEFAULT_CATEGORIES = [
    {"name": "Food & Dining", "icon": "🍔", "color": "#FF6B6B"},
    {"name": "Shopping", "icon": "🛍️", "color": "#4ECDC4"},
    {"name": "Bills & Utilities", "icon": "📄", "color": "#45B7D1"},
    {"name": "Entertainment", "icon": "🎬", "color": "#FFA07A"},
    {"name": "Transportation", "icon": "🚗", "color": "#98D8C8"},
    {"name": "Health & Fitness", "icon": "🏥", "color": "#F7DC6F"},
    {"name": "Education", "icon": "📚", "color": "#BB8FCE"},
    {"name": "Salary", "icon": "💰", "color": "#52BE80"},
    {"name": "Investment", "icon": "📈", "color": "#5DADE2"},
    {"name": "Other", "icon": "📌", "color": "#95A5A6"}
]

SUPPORTED_CURRENCIES = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK"]

# =====================================================
# --------- PAGE ROUTES --------------------------------
# =====================================================

@app.route("/")
def index():
    if "user_id" not in session:
        return render_template("index.html", name=None, balance=0, transactions=[], preferred_currency="INR")

    conn = get_db()
    cur = conn.cursor()

    # Get user's preferred currency
    cur.execute("SELECT preferred_currency FROM users WHERE id=?", (session["user_id"],))
    user = cur.fetchone()
    preferred_currency = user["preferred_currency"] if user else "INR"

    # Summary
    cur.execute("""
        SELECT
            SUM(CASE WHEN type='income' THEN amount_in_base ELSE 0 END) AS income,
            SUM(CASE WHEN type='expense' THEN amount_in_base ELSE 0 END) AS expense
        FROM transactions
        WHERE user_id=?
    """, (session["user_id"],))

    result = cur.fetchone()
    income = result["income"] or 0
    expense = result["expense"] or 0
    balance = income - expense

    # Transactions
    cur.execute("""
        SELECT * FROM transactions
        WHERE user_id=?
        ORDER BY date DESC
    """, (session["user_id"],))

    rows = cur.fetchall()
    transactions = [dict(row) for row in rows]

    conn.close()

    return render_template(
        "index.html",
        name=session.get("user_name"),
        balance=balance,
        transactions=transactions,
        preferred_currency=preferred_currency
    )


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/track")
def track_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("track.html")


@app.route("/history")
def all_transactions():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM transactions
        WHERE user_id=?
        ORDER BY date DESC
    """, (session["user_id"],))

    rows = cur.fetchall()
    transactions = [dict(row) for row in rows]

    conn.close()

    return render_template("history.html", transactions=transactions)


@app.route("/goals")
def goals_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("goals.html")


# =====================================================
# ------------- AUTH APIs ------------------------------
# =====================================================

@app.route("/api/signup", methods=["POST"])
def signup_api():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    preferred_currency = data.get("preferred_currency", "INR")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields required"})

    hashed_password = generate_password_hash(password)

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (name, email, password, preferred_currency)
            VALUES (?, ?, ?, ?)
        """, (name, email, hashed_password, preferred_currency))

        user_id = cur.lastrowid

        # Add default categories for user
        for category in DEFAULT_CATEGORIES:
            cur.execute("""
                INSERT INTO custom_categories (user_id, category_name, icon, color)
                VALUES (?, ?, ?, ?)
            """, (user_id, category["name"], category["icon"], category["color"]))

        conn.commit()
        return jsonify({"success": True})

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Username or Email already exists"
        })

    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login_api():
    data = request.json
    identifier = data.get("identifier")
    password = data.get("password")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM users 
        WHERE email = ? OR name = ?
    """, (identifier, identifier))

    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return jsonify({
            "success": True,
            "redirect": "/"
        })

    return jsonify({"success": False, "message": "Invalid credentials"})


@app.route("/api/logout", methods=["POST"])
def logout_api():
    session.clear()
    return jsonify({"success": True})


# =====================================================
# -------- USER SETTINGS APIs ---------------------------
# =====================================================

@app.route("/api/user/currency", methods=["GET", "POST"])
def user_currency():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    if request.method == "GET":
        cur.execute("SELECT preferred_currency FROM users WHERE id=?", (session["user_id"],))
        user = cur.fetchone()
        conn.close()
        return jsonify({"preferred_currency": user["preferred_currency"]})

    else:  # POST
        data = request.json
        new_currency = data.get("currency", "INR")

        if new_currency not in SUPPORTED_CURRENCIES:
            return jsonify({"success": False, "message": "Unsupported currency"})

        cur.execute("""
            UPDATE users SET preferred_currency=? WHERE id=?
        """, (new_currency, session["user_id"]))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Currency updated"})


@app.route("/api/supported-currencies")
def supported_currencies():
    return jsonify({"currencies": SUPPORTED_CURRENCIES})


# =====================================================
# ------- TRANSACTIONS APIs ----------------------------
# =====================================================

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json

    amount = float(data["amount"])
    currency = data.get("currency", "INR")
    transaction_type = data["type"]

    # Convert to INR (base currency)
    if currency != "INR":
        rate = get_exchange_rate(currency, "INR")
        amount_in_base = amount * rate
    else:
        amount_in_base = amount

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions
        (user_id, type, amount, currency, amount_in_base, category, note, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        transaction_type,
        amount,
        currency,
        amount_in_base,
        data["category"],
        data.get("note", ""),
        data.get("date", datetime.now().strftime("%Y-%m-%d"))
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/transactions/<int:tx_id>", methods=["DELETE"])
def delete_transaction(tx_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM transactions
        WHERE id=? AND user_id=?
    """, (tx_id, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/transactions")
def get_transactions():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM transactions
        WHERE user_id=?
        ORDER BY date DESC
    """, (session["user_id"],))

    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/summary")
def summary():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            SUM(CASE WHEN type='income' THEN amount_in_base ELSE 0 END) AS income,
            SUM(CASE WHEN type='expense' THEN amount_in_base ELSE 0 END) AS expense
        FROM transactions
        WHERE user_id=?
    """, (session["user_id"],))

    result = cur.fetchone()
    conn.close()

    return jsonify({
        "income": result["income"] or 0,
        "expense": result["expense"] or 0
    })





# =====================================================
# ---- CHART DATA APIs --------------------------------
# =====================================================

@app.route("/api/monthly-expense-chart")
def monthly_expense_chart():
    """Graph Data: Last 4 Weeks of Expenses (in base currency)"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            strftime('%W', date) as week_num,
            SUM(amount_in_base) as total
        FROM transactions
        WHERE user_id=? AND type='expense' AND date >= date('now', '-28 days')
        GROUP BY week_num
        ORDER BY week_num
    """, (session["user_id"],))

    rows = cur.fetchall()
    conn.close()

    weeks = []
    totals = []
    
    if rows:
        for row in rows:
            weeks.append(f"Week {row['week_num']}")
            totals.append(row['total'] or 0)
    else:
        weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
        totals = [0, 0, 0, 0]

    return jsonify({
        "labels": weeks,
        "data": totals
    })


@app.route("/api/category-comparison")
def category_comparison():
    """Last Month vs This Month Category-wise Comparison"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    today = datetime.now()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)

    # Last Month Data
    cur.execute("""
        SELECT category, SUM(amount_in_base) as total
        FROM transactions
        WHERE user_id=? AND type='expense' 
              AND date >= ? AND date <= ?
        GROUP BY category
        ORDER BY total DESC
    """, (session["user_id"], last_month_start.strftime("%Y-%m-%d"), last_month_end.strftime("%Y-%m-%d")))

    last_month_data = {row['category']: row['total'] for row in cur.fetchall()}

    # This Month Data
    cur.execute("""
        SELECT category, SUM(amount_in_base) as total
        FROM transactions
        WHERE user_id=? AND type='expense' 
              AND date >= ?
        GROUP BY category
        ORDER BY total DESC
    """, (session["user_id"], current_month_start.strftime("%Y-%m-%d")))

    this_month_data = {row['category']: row['total'] for row in cur.fetchall()}

    conn.close()

    # Get all categories
    all_categories = sorted(set(list(last_month_data.keys()) + list(this_month_data.keys())))

    last_month_values = [last_month_data.get(cat, 0) for cat in all_categories]
    this_month_values = [this_month_data.get(cat, 0) for cat in all_categories]

    return jsonify({
        "categories": all_categories,
        "last_month": last_month_values,
        "this_month": this_month_values
    })


# =====================================================
# -------- GOALS APIs --------------------------------
# =====================================================

@app.route("/api/goals", methods=["GET"])
def get_goals():
    """Get all goals for current month"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    today = datetime.now()
    month = today.month
    year = today.year

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM goals
        WHERE user_id=? AND month=? AND year=?
        ORDER BY category
    """, (session["user_id"], month, year))

    goals = [dict(row) for row in cur.fetchall()]

    # Calculate progress for each goal
    for goal in goals:
        cur.execute("""
            SELECT SUM(amount_in_base) as spent
            FROM transactions
            WHERE user_id=? AND category=? 
                  AND type='expense'
                  AND strftime('%m', date) = ?
                  AND strftime('%Y', date) = ?
        """, (session["user_id"], goal['category'], str(month).zfill(2), str(year)))

        result = cur.fetchone()
        goal['current_amount'] = result['spent'] or 0

    conn.close()

    return jsonify(goals)


@app.route("/api/goals", methods=["POST"])
def create_goal():
    """Create a new goal"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    category = data.get("category")
    target_amount = float(data.get("target_amount", 0))
    currency = data.get("currency", "INR")

    if not category or target_amount <= 0:
        return jsonify({"success": False, "message": "Invalid data"})

    today = datetime.now()
    month = today.month
    year = today.year

    conn = get_db()
    cur = conn.cursor()

    # Check if goal already exists for this category this month
    cur.execute("""
        SELECT id FROM goals
        WHERE user_id=? AND category=? AND month=? AND year=?
    """, (session["user_id"], category, month, year))

    if cur.fetchone():
        return jsonify({"success": False, "message": "Goal already exists for this category this month"})

    cur.execute("""
        INSERT INTO goals (user_id, category, target_amount, currency, month, year)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session["user_id"], category, target_amount, currency, month, year))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    """Delete a goal"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM goals
        WHERE id=? AND user_id=?
    """, (goal_id, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/goals-summary")
def goals_summary():
    """Get goals summary"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    today = datetime.now()
    month = today.month
    year = today.year

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) as total_goals,
               SUM(CASE WHEN current_amount <= target_amount THEN 1 ELSE 0 END) as on_track,
               SUM(CASE WHEN current_amount > target_amount THEN 1 ELSE 0 END) as exceeded
        FROM (
            SELECT g.*, 
                   COALESCE(SUM(t.amount_in_base), 0) as current_amount
            FROM goals g
            LEFT JOIN transactions t ON g.user_id = t.user_id 
                                     AND g.category = t.category
                                     AND t.type = 'expense'
                                     AND strftime('%m', t.date) = ?
                                     AND strftime('%Y', t.date) = ?
            WHERE g.user_id = ? AND g.month = ? AND g.year = ?
            GROUP BY g.id
        )
    """, (str(month).zfill(2), str(year), session["user_id"], month, year))

    result = cur.fetchone()
    conn.close()

    return jsonify({
        "total_goals": result['total_goals'] or 0,
        "on_track": result['on_track'] or 0,
        "exceeded": result['exceeded'] or 0
    })


# =====================================================
# ---------- RUN ----------------------------------------
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)