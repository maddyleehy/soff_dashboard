#import sqlite3
#
#conn = sqlite3.connect("vehicle_history.db")
#conn.execute("ALTER TABLE bucket_history ADD COLUMN sub_bucket_nm TEXT")
#conn.execute("ALTER TABLE bucket_history ADD COLUMN status_nm TEXT")
#conn.commit()
#conn.close()
#print("Columns added")



import sqlite3
import pandas as pd

conn = sqlite3.connect("vehicle_history.db")
#
#master_df = pd.read_csv("data/master_codes.csv", dtype=str)
#master_df.columns = master_df.columns.str.strip()
#code_dict = dict(zip(master_df["Code"], master_df["English"]))
#
#rows = conn.execute("SELECT id, sub_bucket, status FROM bucket_history").fetchall()
#
#conn.executemany(
#    "UPDATE bucket_history SET sub_bucket_nm = ?, status_nm = ? WHERE id = ?",
#    [(code_dict.get(sb), code_dict.get(st), row_id) for row_id, sb, st in rows],
#)
#conn.commit()
#conn.close()



conn.execute("""
    UPDATE defect_history
    SET unique_id = body_no || '_' || sub_proc_cd || '_' || inspec_part_cd || '_' || fault_cd  || '_' || dtl_part_cd || '_' || stn_cd || '_' || fault_input_dt
""")
conn.commit()
conn.close()
