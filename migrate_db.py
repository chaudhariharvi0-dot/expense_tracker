import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DATABASE_NAME", "spendwise.db")

def migrate_database():
    """Add missing columns for multi-currency and custom categories support"""
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        print("🔄 Starting database migration... - migrate_db.py:16")
        
        # ========== USERS TABLE MIGRATION ==========
        print("\n1️⃣ Adding preferred_currency to users table... - migrate_db.py:19")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN preferred_currency TEXT DEFAULT 'INR'")
            print("✅ Added preferred_currency column - migrate_db.py:22")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("⚠️ Column already exists, skipping... - migrate_db.py:25")
            else:
                raise
        
        # ========== TRANSACTIONS TABLE MIGRATION ==========
        print("\n2️⃣ Adding currency columns to transactions table... - migrate_db.py:30")
        try:
            cur.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'INR'")
            print("✅ Added currency column - migrate_db.py:33")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("⚠️ Column already exists, skipping... - migrate_db.py:36")
            else:
                raise
        
        try:
            cur.execute("ALTER TABLE transactions ADD COLUMN amount_in_base REAL DEFAULT 0")
            print("✅ Added amount_in_base column - migrate_db.py:42")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("⚠️ Column already exists, skipping... - migrate_db.py:45")
            else:
                raise
        
        # ========== GOALS TABLE MIGRATION ==========
        print("\n3️⃣ Adding currency column to goals table... - migrate_db.py:50")
        try:
            cur.execute("ALTER TABLE goals ADD COLUMN currency TEXT DEFAULT 'INR'")
            print("✅ Added currency column to goals - migrate_db.py:53")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("⚠️ Column already exists, skipping... - migrate_db.py:56")
            else:
                raise
        
       
        
        # ========== UPDATE EXISTING TRANSACTIONS ==========
        print("\n5️⃣ Updating existing transactions with base amounts... - migrate_db.py:63")
        cur.execute("""
        UPDATE transactions 
        SET amount_in_base = amount,
            currency = 'INR'
        WHERE amount_in_base IS NULL OR amount_in_base = 0
        """)
        print(f"✅ Updated transactions")
        
        
        # Get all user IDs
        cur.execute("SELECT id FROM users")
        user_ids = cur.fetchall()
        
        for user_id in user_ids:
            uid = user_id[0]
            for cat_name, icon, color in DEFAULT_CATEGORIES:
                try:
                    cur.execute("""
                    INSERT OR IGNORE INTO custom_categories 
                    (user_id, category_name, icon, color)
                    VALUES (?, ?, ?, ?)
                    """, (uid, cat_name, icon, color))
                except Exception as e:
                    pass  # Ignore duplicates
        
        print(f"✅ Added default categories for {len(user_ids)} users")
        
        conn.commit()
        print("\n" + "="*50)
        print("✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Migration Error: {str(e)}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()