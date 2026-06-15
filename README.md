# 💰 SpendWise — Personal Finance Tracker

Track your expenses, set budget goals, and master your money — all in one place.

SpendWise is a full-stack personal finance web app built with **Flask + SQLite**. It supports multi-currency tracking, category-wise budget goals, visual analytics charts, and secure user authentication.

---

## ✨ Features

- **Budget Goals** — Set monthly spending limits per category; track on-track vs exceeded goals
- **Visual Analytics** — Weekly expense trend chart + last month vs this month category comparison
- **Transaction Management** — Add income/expense with category, date, note, and currency; delete transactions
- **User Authentication** — Secure signup/login with hashed passwords
- **Responsive UI** — Dark glassmorphism design using Tailwind CSS + Font Awesome

---

## 🛠️ Tech Stack

Backend : Python, Flask 
Database : SQLite 
Frontend : HTML, CSS, JavaScript 
Charts : Chart.js 

---

## 📁 Project Structure

```
SpendWise/
├── app.py                 
├── spendwise.db            
├── migrate_db.py          
├── check_db.py             
├── requirements.txt       
├── .env                    
│
├── templates/
│   ├── index.html          
│   ├── login.html         
│   ├── signup.html        
│   ├── track.html          
│   ├── history.html        
│   ├── all-transactions.html  
│   ├── goals.html          
│   └── home.html          
│
└── static/
    ├── css/
    │   └── index.css       
    └── js/
        └── index.js       
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/spendwise.git
cd spendwise
```

### 2. Create & Activate Virtual Environment
```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — Linux / Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file in the root folder:
```
SECRET_KEY=your_secret_key_here
DATABASE_NAME=spendwise.db
```

> ⚠️ Never commit your `.env` file. It's already in `.gitignore`.

### 5. Run the App
```bash
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000/**

### 6. (Optional) Run DB Migration

If you're upgrading from an older version of SpendWise:
```bash
python migrate_db.py
```

Or to just check/fix the schema:
```bash
python check_db.py
```

---

## 🗄️ Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary Key |
| name | TEXT | Unique username |
| email | TEXT | Unique email |
| password | TEXT | Hashed (Werkzeug) |
| preferred_currency | TEXT | Default: INR |
| created_at | TEXT | Auto timestamp |

### `transactions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary Key |
|user_id | INTEGER | FK → users |
| type | TEXT | `income` or `expense` |
| amount | REAL | Original amount |
| currency | TEXT | Original currency |
| amount_in_base | REAL | Converted to INR |
| category | TEXT | e.g. Food, Shopping |
| note | TEXT | Optional |
| date | TEXT | YYYY-MM-DD |

### `goals`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary Key |
| user_id | INTEGER | FK → users |
| category | TEXT | Budget category |
| target_amount | REAL | Spending limit |
| current_amount | REAL | Auto-calculated |
| currency | TEXT | Default: INR |
| month / year | INTEGER | Goal period |
| status | TEXT | `active` |

### `custom_categories`
Stores per-user categories with emoji icons and hex color codes.

---

## 🔌 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/signup` | Create new account |
| POST | `/api/login` | Login with email/username + password |
| GET | `/logout` | Clear session & logout |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions` | Get all user transactions |
| POST | `/api/transactions` | Add new transaction |
| DELETE | `/api/transactions/<id>` | Delete a transaction |
| GET | `/api/summary` | Total income & expense |

### Goals
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/goals` | Get current month's goals |
| POST | `/api/goals` | Create a new budget goal |
| DELETE | `/api/goals/<id>` | Delete a goal |
| GET | `/api/goals-summary` | Total / on-track / exceeded count |

### Charts & Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/monthly-expense-chart` | Weekly expense data (last 28 days) |
| GET | `/api/category-comparison` | Last month vs this month by category |
| GET | `/api/user/currency` | Get user's preferred currency |

### Pages
| Route | Description |
|---|---|
| `/` | Dashboard (login required) |
| `/login` | Login page |
| `/signup` | Signup page |
| `/track` | Add transaction (login required) |
| `/history` | Full transaction history (login required) |
| `/goals` | Budget goals page (login required) |

---


## 📦 Dependencies

```
flask
flask-cors
python-dotenv
werkzeug
requests
```

Install all with:
```bash
pip install -r requirements.txt
```

> **Note:** Python 3.8+ recommended.

---

## 🔒 Security Notes

- Passwords are hashed using `werkzeug.security.generate_password_hash`
- Sessions are server-side (Flask sessions with a `SECRET_KEY`)
- SQL queries use parameterized statements (no SQL injection risk)
- `.env` and `*.db` files are excluded via `.gitignore`

---

## 🐛 Known Issues & Bugs

- `goals.html` — `goalCategory` input field is referenced in JS but not present in the HTML form 
- `history.html` — Delete button uses `['id']` string literal instead of `tx.id` 
- `migrate_db.py` — References `DEFAULT_CATEGORIES` variable that is not defined in that file
- `check_db.py` — Debug print statements contain raw line numbers 

---

## 🚀 Future Improvements

- Export transactions to CSV / PDF
- Email notifications when budget goal is exceeded
- Mobile app

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙋 Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.
