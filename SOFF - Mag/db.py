import pandas as pd
import sqlite3
from datetime import datetime

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
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                body_no TEXT NOT NULL,
                seq TEXT,
                station TEXT,
                work_no TEXT,
                facility TEXT,
                inspection_date TEXT,
                facility_inspec_count TEXT,
                total_result TEXT,
                last_result TEXT,
                repairer TEXT,
                repair_location TEXT,
                repair_date TEXT,
                repair_yn TEXT,
                defect_desc TEXT,
                memo TEXT,
                confirmer TEXT,
                confirm_date TEXT,
                detail_work TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()



# =====================================
# LOAD AND APPEND CSV DATA
# =====================================

def load_bucket_csv_to_db(csv_file_path):
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

def load_repair_csv_to_db(csv_file_path):
    df = pd.read_csv(csv_file_path)

    df.columns = df.columns.str.strip()
    print(df.columns.tolist())
    df.rename(
        columns={
            "BODY NO": "body_no",
            "SEQ": "seq",
            "Station": "station",
            "Work No": "work_no",
            "Facility": "facility",
            "Inspection Date": "inspection_date",
            "Facility Inspec Count": "facility_inspec_count",
            "Total Result": "total_result",
            "Last Result": "last_result",
            "Repairer": "repairer",
            "Repair Location": "repair_location",
            "Repair date": "repair_date",
            "Repair Y/N": "repair_yn",
            "Defect Desc": "defect_desc",
            "Memo": "memo",
            "Confirmer": "confirmer",
            "Confirm date": "confirm_date",
            "Detail Work": "detail_work"
        },
        inplace=True
    )

    df["last_updated"] = datetime.now()

    df.to_sql(
        "repair_history",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    return len(df)

