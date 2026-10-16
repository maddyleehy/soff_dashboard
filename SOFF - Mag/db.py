import pandas as pd
import sqlite3
from datetime import datetime
from utils import get_bucket

# =====================================
# INITIALIZE DATABASE TABLE
# =====================================

def get_db_connection():
    return sqlite3.connect(
        "vehicle_history.db",
        check_same_thread=False
    )

conn = get_db_connection()

def init_db():
    """Create tables if they don't exist"""

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bucket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body_no TEXT NOT NULL,
            bucket TEXT,
            sub_bucket TEXT,
            status TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

init_db()


# =====================================
# LOAD AND APPEND CSV DATA
# =====================================

def load_csv_to_db(csv_file_path):
    """Load CSV and APPEND to database (keeps old data)"""
    
    # Load CSV
    df = pd.read_csv(csv_file_path)

    # Remove white spaces from columns
    df.columns = df.columns.str.strip()
    # Bucket logic
     #new column named bucket = obtain loc_cd from get_bucket function
    df["last_updated"] = datetime.now() #new column name last_updated = current time
    
    # Rename columns to match database
    df.rename(columns={"BODY_NO": "body_no", "BUCKET": "bucket", "SUB_BUCKET": "sub_bucket", "STATUS": "status"}, inplace=True)
    
    # APPEND to database (keeps old data)
    df.to_sql(
        "bucket_history",
        conn,
        if_exists='append',  # ✅ APPEND instead of REPLACE
        index=False
    )
    conn.commit()
    
    return len(df)

# Load all records from SQLite
df = pd.read_sql("""
SELECT *
FROM bucket_history
""", conn)


