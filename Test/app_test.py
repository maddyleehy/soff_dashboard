import pandas as pd
import sqlite3
from datetime import datetime
from tkinter import Tk, filedialog
import os
from utils_test import repair_status_def


# =====================================
# INITIALIZE DATABASE TABLE
# =====================================

def get_db_connection():
    return sqlite3.connect(
        "repair_status.db",
        check_same_thread=False
    )

conn = get_db_connection()

def init_db():
    """Create tables if they don't exist"""
    cursor = conn.cursor()

    # ✅ DROP OLD TABLE , will always delete old table
    #cursor.execute("DROP TABLE IF EXISTS repair_status")
    
    # ✅ CREATE NEW TABLE WITH COLUMNS FROM CSV AND NEW REPAIR_STATUS COLUMN
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repair_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            UNIQUE_ID TEXT NOT NULL, 
            BODY_NO TEXT NOT NULL,
            FAULT_INPUT_DT DATETIME,
            REPAIR_START_DT DATETIME,
            REPAIR_END_DT DATETIME,
            CONFIRM_DT DATETIME,
            REPAIR_STATUS TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ✅ COMMIT TABLE CREATION
    conn.commit()
    print("✅ Database table created")

init_db()


# =====================================
# LOAD AND APPEND CSV DATA
# =====================================

def load_csv_to_db(csv_file_path):
    """Load CSV and APPEND to database"""
    try:
        df = pd.read_csv(csv_file_path)     #pandas function to read csv file
        df.columns = df.columns.str.strip() #trim down csv column name

        # ✅ SELECT ONLY THE COLUMNS YOU NEED
        required_columns = [
            "UNIQUE_ID", 
            "BODY_NO", 
            "FAULT_INPUT_DT", 
            "REPAIR_START_DT", 
            "REPAIR_END_DT", 
            "CONFIRM_DT"
        ]

        # Keep only required columns (case-insensitive matching)
        #df.columns = df.columns.str.lower()
        df = df[required_columns]    
        
        df["REPAIR_STATUS"] = df.apply(
            lambda row: repair_status_def(
                row["REPAIR_START_DT"], 
                row["REPAIR_END_DT"], 
                row["CONFIRM_DT"]
            ), 
            axis=1
        )

        #Add current timestamp
        df["last_updated"] = datetime.now()

        print(f"📊 Inserting {len(df)} rows...")
        
        # Insert into database
        df.to_sql('repair_status', conn, if_exists='append', index=False)
        
        # ✅ CRITICAL: COMMIT CHANGES TO SAVE TO DISK
        conn.commit()
        
        print("✅ Data committed to database")
        
        return len(df)
        

    except FileNotFoundError:
        print(f"❌ Error: File not found!")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 0


def select_csv_file():
    """Open file dialog to select CSV file"""
    root = Tk()
    root.withdraw()  # Hide the root window
    
    # Open file dialog
    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    return file_path

# ===== EXECUTE =====
init_db()

# Open file dialog
selected_file = select_csv_file()

if selected_file:
    print(f"Selected file: {selected_file}")
    rows_loaded = load_csv_to_db(selected_file)
    print(f"✅ Loaded {rows_loaded} rows into database")
else:
    print("❌ No file selected")



    # ✅ CLOSE CONNECTION WHEN DONE
conn.close()
print("✅ Database connection closed")