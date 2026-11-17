
# =====================================
# ADDING NEW COLUMNS
# =====================================

#import sqlite3
#conn = sqlite3.connect("vehicle_history.db")
#
#new_columns = {
#    "prod_part_status":"TEXT",
#    "prod_pending_count":"INTEGER",
#    "prod_supplied_count":"INTEGER",
#    "repair_part_status":"TEXT",
#    "repair_pending_count":"INTEGER",
#    "repair_supplied_count":"INTEGER",
#}
#existing = {row[1] for row in conn.execute("PRAGMA table_info(dahsboard_summary)")}
#
#for name, col_type in new_columns.items():
#    if name in existing:
#        print(f"skipped {name} (already exist)")
#        continue
#    conn.execute(f"ALTER TABLE dashboard_summary ADD COLUMN {name} {col_type}")
#    print (f"added {name}")
#
#conn.commit()
#conn.close()
#print("Columns added")

# =====================================
# RENAME COLUMNS
# =====================================
#import sqlite3
#
#conn = sqlite3.connect("vehicle_history.db")
#conn.execute("ALTER TABLE repair_status RENAME COLUMN remark TO remarks")
#conn.commit()
#conn.close()
#print("Columns renamed")

# =====================================
# BACKFILL
# =====================================


import sqlite3
import pandas as pd

conn = sqlite3.connect("vehicle_history.db")

#master_df = pd.read_csv("data/employee_master_list.csv", dtype=str)
#master_df.columns = master_df.columns.str.strip()
#code_dict = dict(zip(master_df["User/Employee ID"], master_df["First Name"]))

rows = conn.execute("SELECT id, inspector_id, repairer_id, confirmer_id FROM defect_history").fetchall()

conn.executemany(
    "UPDATE defect_history SET file_name = ? WHERE id = ?",
    [(code_dict.get(insp), code_dict.get(rep), code_dict.get(conf), row_id) for row_id, insp, rep, conf in rows],
)
conn.commit()
conn.close()

# =====================================
# initial script given
# =====================================
#from datetime import datetime, timezone
#import pandas as pd
#import sqlite3
#
#DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
#DATE_FORMAT = "%Y-%m-%d"
#
#def to_db_datetime(value, date_only=False):
#    """
#    Convert a raw value to 'YYYY-MM-DD HH:MM:SS' (or 'YYYY-MM-DD' if date_only).
#    Supports:
#      - 14 digits  -> YYYYMMDDhhmmss   (e.g. 20261005142201)
#      - 13 digits  -> epoch milliseconds, UTC (e.g. 1791880000000)
#      - 8 digits   -> YYYYMMDD         (e.g. 20261005)
#      - Text dates -> parsed by pandas (e.g. 2026-10-05 14:22:01)
#    Returns None for blanks or unparseable values.
#    """
#    if pd.isna(value):
#        return None
#
#    s = str(value).strip()
#    if s.endswith(".0"):            # Excel/float artifact: 20261005142201.0
#        s = s[:-2]
#    if s == "" or s.lower() in ("null", "nan", "none"):
#        return None
#
#    try:
#        if s.isdigit():
#            if len(s) == 14:
#                dt = datetime.strptime(s, "%Y%m%d%H%M%S")
#            elif len(s) == 13:
#                dt = datetime.fromtimestamp(int(s) / 1000, tz=timezone.utc).replace(tzinfo=None)
#            elif len(s) == 8:
#                dt = datetime.strptime(s, "%Y%m%d")
#            else:
#                return None
#        else:
#            parsed = pd.to_datetime(s, errors="coerce")
#            if pd.isna(parsed):
#                return None
#            dt = parsed.to_pydatetime()
#    except ValueError:
#        return None
#
#    return dt.strftime(DATE_FORMAT if date_only else DATETIME_FORMAT)
#
#DB_PATH = "vehicle_history.db"
#TABLE = "defect_history"
#
#DATETIME_COLS = [
#    "fault_input_dt", "repair_dt", "repair_start_dt", "repair_end_dt",
#    "confirm_dt", "main_inspec_dt", "reg_dt", "chg_dt",
#]
#DATE_COLS = ["fault_input_date", "main_inspec_date"]
#
#conn = sqlite3.connect(DB_PATH)
#
## 1. Confirm the columns exist before changing anything
#existing = {row[1] for row in conn.execute(f"PRAGMA table_info({TABLE})")}
#missing = [c for c in DATETIME_COLS + DATE_COLS if c not in existing]
#if missing:
#    raise SystemExit(f"Columns not found in {TABLE}: {missing}")
#
## 2. Read the table (values stay as stored; to_db_datetime handles the formats)
#df = pd.read_sql(f"SELECT id, {', '.join(DATETIME_COLS + DATE_COLS)} FROM {TABLE}", conn)
#
## 3. Convert
#for col in DATETIME_COLS:
#    df[col] = df[col].map(to_db_datetime)
#for col in DATE_COLS:
#    df[col] = df[col].map(lambda v: to_db_datetime(v, date_only=True))
#
## 4. Write back, matched by primary key
#cols = DATETIME_COLS + DATE_COLS
#set_clause = ", ".join(f"{c} = ?" for c in cols)
#params = [tuple(row[c] for c in cols) + (row["id"],) for _, row in df.iterrows()]
#
#conn.executemany(f"UPDATE {TABLE} SET {set_clause} WHERE id = ?", params)
#conn.commit()
#print(f"Updated {len(df)} rows")
#conn.close()
#

#python add_columns.py