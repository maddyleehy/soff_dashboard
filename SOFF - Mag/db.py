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

#create tables with header name and respective data type
    #Bucket db table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS bucket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body_no TEXT NOT NULL,
            bucket TEXT,
            sub_bucket TEXT,
            sub_bucket_nm TEXT,
            status TEXT,
            status_nm TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(body_no, bucket, sub_bucket, status)
        )
    """)

    #Defect db table
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS defect_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_id TEXT,
                body_no TEXT NOT NULL,
                main_proc_cd TEXT,
                sub_proc_cd TEXT,
                inspec_part_cd TEXT,
                inspec_part_nm TEXT,
                fault_cd TEXT,
                fault_nm TEXT,
                dtl_part_cd TEXT,
                dtl_part_nm TEXT,
                use_yn TEXT,
                stn_grp_cd TEXT,
                stn_grp_nm TEXT,
                stn_cd TEXT,
                stn_nm TEXT,
                fault_input_type TEXT,
                fault_type TEXT,
                inspector_id TEXT,
                fault_input_date TEXT,
                fault_input_dt TEXT,
                inspec_info_yn TEXT,
                round_cd TEXT,
                repair_yn TEXT,
                repair_dt TEXT,
                repairer_id TEXT,
                repair_site_cd TEXT,
                repair_info_yn TEXT,
                repair_start_dt TEXT,
                repair_end_dt TEXT,
                confirm_yn TEXT,
                confirm_dt TEXT,
                confirmer_id TEXT,
                resp1_cd TEXT,
                resp2_cd TEXT,
                main_inspec_date TEXT,
                main_inspec_dt TEXT,
                reg_id TEXT,
                reg_dt TEXT,
                chg_id TEXT,
                chg_dt TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    #Parts ETA db table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS parts_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body_no TEXT NOT NULL,
            part_no TEXT,
            part_name TEXT,
            eta DATETIME,
            status TEXT,
            cell_cd TEXT,
            text TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
    """)
    
    # Create DB Table for Dashboard Summary
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dashboard_summary(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        body_no TEXT,
        bucket TEXT,
        sub_bucket TEXT,
        status TEXT,
        defect_count INTEGER,
        repair_started INTEGER,
        repair_completed INTEGER,
        quality_accepted INTEGER,
        vehicle_status TEXT,
        snapshot_dt DATETIME
    )

    """
    )

    conn.commit()

# =====================================
# CONVERTS EPOCH/INTEGER TO DT FORMAT
# =====================================

def normalize_datetime(value):
    """Convert any supported raw format to 'YYYY-MM-DD HH:MM:SS' (or date-only)."""
    if pd.isna(value):
        return None
    s = str(value).strip().removesuffix(".0")
    if not s or not s.isdigit():
        return None
    if len(s) == 14:                      # 20260911104917
        return datetime.strptime(s, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    if len(s) == 13:                      # 1791880000000 (epoch ms, UTC)
        return pd.to_datetime(int(s), unit="ms").strftime("%Y-%m-%d %H:%M:%S")
    if len(s) == 8:                       # 20261013
        return datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d")
    return None                           # unknown format: store NULL and inspect


# =====================================
# LOAD AND APPEND CSV DATA (Bucket)
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

    # Map code to description using master tables
    master_df = pd.read_csv("data/master_codes.csv")
    master_df.columns = master_df.columns.str.strip()
    code_dict = dict(zip(master_df["Code"].astype(str), master_df["English"]))
    df["sub_bucket_nm"] = df["sub_bucket"].map(code_dict)
    df["status_nm"] = df["status"].map(code_dict)
    df["last_updated"] = datetime.now()
    
    df.to_sql(
        "bucket_history",
        conn,
        if_exists="append",
        index=False
    )
    conn.commit()
    
    return len(df)
  
    

# =====================================
# LOAD AND APPEND CSV DATA (Defect)
# =====================================

def load_defect_csv_to_db(csv_file_path):
    df = pd.read_csv(csv_file_path)
    df.columns = df.columns.str.strip()
    keep_cols = ["UNIQUE_ID",
        "BODY_NO",
        "MAIN_PROC_CD",
        "SUB_PROC_CD",
        "INSPEC_PART_CD",
        "FAULT_CD",
        "DTL_PART_CD",
        "USE_YN",
        "STN_GRP_CD",
        "STN_CD",
        "FAULT_INPUT_TYPE",
        "FAULT_TYPE",
        "INSPECTOR_ID",
        "FAULT_INPUT_DATE",
        "FAULT_INPUT_DT",
        "INSPEC_INFO_YN",
        "ROUND_CD",
        "REPAIR_YN",
        "REPAIR_DT",
        "REPAIRER_ID",
        "REPAIR_SITE_CD",
        "REPAIR_INFO_YN",
        "REPAIR_START_DT",
        "REPAIR_END_DT",
        "CONFIRM_YN",
        "CONFIRM_DT",
        "CONFIRMER_ID",
        "RESP1_CD",
        "RESP2_CD",
        "MAIN_INSPEC_DATE",
        "MAIN_INSPEC_DT",
        "REG_ID",
        "REG_DT",
        "CHG_ID",
        "CHG_DT"]
    df = df[keep_cols]
    df.columns = [col.lower() for col in df.columns]

    # Map code to description using master tables
    master_df = pd.read_csv("data/master_codes.csv")
    master_df.columns = master_df.columns.str.strip()

    code_dict = dict(zip(master_df["Code"].astype(str), master_df["English"]))

    cols = ["body_no", "sub_proc_cd", "inspec_part_cd", "fault_cd", "dtl_part_cd", "stn_cd", "fault_input_dt"]
    df["unique_id"] = df[cols].fillna("").astype(str).agg("_".join, axis=1)

    df["inspec_part_nm"] = df["inspec_part_cd"].map(code_dict)
    df["fault_nm"] = df["fault_cd"].map(code_dict)
    df["dtl_part_nm"] = df["dtl_part_cd"].map(code_dict)
    df["stn_grp_nm"] = df["stn_grp_cd"].map(code_dict)
    df["stn_nm"] = df["stn_cd"].map(code_dict)
    df["last_updated"] = datetime.now()
    df.to_sql(
        "defect_history",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    return len(df)


# =====================================
# LOAD AND APPEND CSV DATA (Parts)
# =====================================

def load_parts_csv_to_db(csv_file_path):
    df = pd.read_csv(csv_file_path)
    df.columns = df.columns.str.strip()
    keep_cols = ["status",
        "eta",
        "body_no",
        "part_no",
        "part_name",
        "cell_cd",
        "text"
        ]
    df = df[keep_cols]
   
    df.columns = [col.lower() for col in df.columns]
    df.to_sql(
        "parts_history",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    return len(df)

# =====================================
# Dashboard summary DB
# =====================================



def load_dashboard_summary_to_db(summary_df):
    summary_df.to_sql(
        "dashboard_summary",
        conn,
        if_exists = "replace",
        index=False
    )
    conn.commit()