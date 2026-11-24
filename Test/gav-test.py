import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

conn = sqlite3.connect("vehicle_history.db")


def get_file_suffix(file_path, length = 13):
    """Return the last 'length' characters of the file name, excluding .csv.
    Accepts a pthe string, a Pth, or a streamlit uploaded file. """
    #if getattr(file_path, "name", file_path) <> 
    name = getattr(file_path, "name", file_path) # UploadedFile/Path -> .name, str stays as-is
    name_float = float(Path(name).stem[-length])
    return Path(name).stem[-length:],name_float

def load_bucket_csv_to_db(csv_file_path):
    """Load CSV and APPEND to database (keeps old data)"""
    
    # Load CSV
    df = pd.read_csv(csv_file_path)

    # Remove white spaces from columns
    df.columns = df.columns.str.strip()
    
    # Bucket logic
     #new column named bucket = obtain loc_cd from get_bucket function
    df["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #new column name last_updated = current time 
    
    # Rename columns to match database
    df.rename(columns={"BODY_NO": "body_no", "BUCKET": "bucket", "SUB_BUCKET": "sub_bucket", "STATUS": "status"}, inplace=True)

    # Map code to description using master tables
    master_df = pd.read_csv("data/master_codes.csv")
    master_df.columns = master_df.columns.str.strip()
    code_dict = dict(zip(master_df["Code"].astype(str), master_df["English"]))
    df["sub_bucket_nm"] = df["sub_bucket"].map(code_dict)
    df["status_nm"] = df["status"].map(code_dict)
    df["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    df = sort_by_te1(df, conn)
    df.to_sql(
        "bucket_history",
        conn,
        if_exists="append",
        index=False
    )
    conn.commit()
    
    return len(df)  

def load_parts_csv_to_db(csv_file_path):
    get_file_suffix(csv_file_path)
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
    df["eta"] = pd.to_datetime(
        df["eta"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    df["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.columns = [col.lower() for col in df.columns]
    
    df = sort_by_te1(df, conn)
    df.to_sql(
        "parts_history",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    return len(df)

testA=get_file_suffix("C:\\Users\\HMGICS\\OneDrive - HyundaiMotorAPAC\\Desktop backup\\Working Files\\GIT files\\soff_dashboard\\SOFF - Mag\\data\\bucket_status_261028_170143.csv")
print(type(testA))
#target_path = 'C:\Users\HMGICS\OneDrive - HyundaiMotorAPAC\Desktop backup\Working Files\GIT files\soff_dashboard\SOFF - Mag\data\bucket_status_261028_170143.csv'