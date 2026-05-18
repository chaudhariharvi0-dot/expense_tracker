import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_NAME = os.getenv("DATABASE_NAME", "spendwise.db")

def check_and_fix():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    print("= - check_db.py:12" * 60)
    print("CHECKING DATABASE SCHEMA - check_db.py:13")
    print("= - check_db.py:14" * 60)
    
    # Check transactions table
    print("\n📋 TRANSACTIONS TABLE: - check_db.py:17")
    cur.execute("PRAGMA table_info(transactions)")
    columns = cur.fetchall()
    
    has_currency = False
    has_amount_in_base = False
    
    for col in columns:
        print(f"✓ {col[1]:20}  {col[2]} - check_db.py:25")
        if col[1] == 'currency':
            has_currency = True
        if col[1] == 'amount_in_base':
            has_amount_in_base = True
    
    print("\n - check_db.py:31" + "=" * 60)
    print("MISSING COLUMNS CHECK: - check_db.py:32")
    print("= - check_db.py:33" * 60)
    
    if not has_currency:
        print("❌ Missing: currency column  ADDING NOW... - check_db.py:36")
        try:
            cur.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR'")
            conn.commit()
            print("✅ Added currency column - check_db.py:40")
        except Exception as e:
            print(f"⚠️ Error: {e} - check_db.py:42")
    else:
        print("✅ currency column exists - check_db.py:44")
    
    if not has_amount_in_base:
        print("❌ Missing: amount_in_base column  ADDING NOW... - check_db.py:47")
        try:
            cur.execute("ALTER TABLE transactions ADD COLUMN amount_in_base REAL DEFAULT 0")
            conn.commit()
            print("✅ Added amount_in_base column - check_db.py:51")
        except Exception as e:
            print(f"⚠️ Error: {e} - check_db.py:53")
    else:
        print("✅ amount_in_base column exists - check_db.py:55")
    
    # Also check users table
    print("\n📋 USERS TABLE: - check_db.py:58")
    cur.execute("PRAGMA table_info(users)")
    users_cols = cur.fetchall()
    
    has_pref_currency = False
    for col in users_cols:
        print(f"✓ {col[1]:20}  {col[2]} - check_db.py:64")
        if col[1] == 'preferred_currency':
            has_pref_currency = True
    
    if not has_pref_currency:
        print("\n❌ Missing: preferred_currency column  ADDING NOW... - check_db.py:69")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN preferred_currency TEXT DEFAULT 'INR'")
            conn.commit()
            print("✅ Added preferred_currency column - check_db.py:73")
        except Exception as e:
            print(f"⚠️ Error: {e} - check_db.py:75")
    else:
        print("\n✅ preferred_currency column exists - check_db.py:77")
    
    print("\n - check_db.py:79" + "=" * 60)
    print("✅ DATABASE CHECK COMPLETE! - check_db.py:80")
    print("= - check_db.py:81" * 60)
    
    conn.close()

if __name__ == "__main__":
    check_and_fix()