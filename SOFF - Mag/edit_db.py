#import sqlite3
#
#conn = sqlite3.connect("vehicle_history.db")
#cursor = conn.cursor()
#cursor.execute("DROP TABLE IF EXISTS master_te1")
##cursor = conn.cursor()
##cursor.execute('''
##UPDATE parts_history
##SET eta = substr(eta, 1, 10)
##    '''
##)
#
#conn.commit()
#conn.close()
#print("Timestamps updated successfully.")

## =====================================
## DB backup
## =====================================
#
#import sqlite3
#
#conn = sqlite3.connect("vehicle_history.db")
#
#print("=== Tables ===")
#print([r[0] for r in conn.execute(
#    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
#
#print("\n=== Row counts ===")
#for t in ["bucket_history", "defect_history", "parts_history", "dashboard_summary"]:
#    try:
#        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
#    except sqlite3.OperationalError as e:
#        print(t, "ERROR:", e)
#
#print("\n=== Duplicate defect rows (same unique_id and load time) ===")
#print(conn.execute("""
#    SELECT COUNT(*) FROM (
#        SELECT unique_id, last_updated FROM defect_history
#        GROUP BY unique_id, last_updated HAVING COUNT(*) > 1)
#""").fetchone()[0])
#
#print("\n=== Loads per upload time (defect) ===")
#print(conn.execute("""
#    SELECT last_updated, COUNT(*) FROM defect_history
#    GROUP BY last_updated ORDER BY last_updated DESC LIMIT 10
#""").fetchall())
#
#print("\n=== Unparseable or non-standard date values ===")
#print(conn.execute("""
#    SELECT COUNT(*) FROM defect_history
#    WHERE fault_input_dt IS NOT NULL AND fault_input_dt <> ''
#      AND fault_input_dt NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'
#""").fetchone()[0])
#
#print("\n=== Bucket values that look wrong ===")
#print(conn.execute("""
#    SELECT bucket, COUNT(*) FROM bucket_history
#    GROUP BY bucket ORDER BY COUNT(*) DESC
#""").fetchall())
#
#print("\n=== Table columns (defect_history) ===")
#print([r[1] for r in conn.execute("PRAGMA table_info(defect_history)")])
#
#conn.close()


# =====================================
# Remove DB
# =====================================
#import os
#os.remove("vehicle_history.db")
#print("Deleted vehicle_history.db")

# =====================================
# Run this after removing DB
# =====================================
#import sqlite3
#TABLES_TO_DROP = [
   # "dashboard_summary",
    #"bucket_history",
    #"defect_history",
   # "parts_history",

#]

#conn = sqlite3.connect("vehicle_history.db")
#for table in TABLES_TO_DROP:
#    conn.execute(f"DROP TABLE IF EXISTS {table}")
#    print ("dropped", table)
#
##conn.execute("DROP TABLE IF EXISTS bucket_history")
#conn.commit()
#conn.close()


# =====================================
# Troubleshooting
# =====================================

#import sqlite3
#conn = sqlite3.connect("vehicle_history.db")
#print(conn.execute(
#    "SELECT sql FROM sqlite_master WHERE name = 'bucket_history'"
#).fetchone()[0])
#conn.close()



#legacy load
#UPDATE defect_history
#SET file_name = 'vehicle_defects_20240115'
#WHERE last_updated = '2024-01-15 09:30:00'
#  AND file_name IS NULL;



#import sqlite3
#
#conn = sqlite3.connect("data/vehicles.db")  # adjust to your database
#cur = conn.cursor()
#cur.execute(
#    """
#    UPDATE defect_history
#    SET file_name = ?
#    WHERE last_updated = ? AND file_name IS NULL
#    """,
#    ("vehicle_defects_20240115", "2024-01-15 09:30:00"),
#)
#conn.commit()
#print(f"Updated {cur.rowcount} rows")
#conn.close()


# =====================================
# replace value in db
# =====================================
import shutil
import sqlite3

conn = sqlite3.connect("vehicle_history.db")

##check the content of file_name
#print(conn.execute("""
#    SELECT file_name, COUNT(*)
#    FROM defect_history
#    WHERE file_name like '%legacy%'
#    GROUP BY file_name
#""").fetchall())
#conn.close




cur = conn.execute (
    "UPDATE defect_history SET file_name = ? where file_name = ?",
    ("0", "legacy_load"),
)
conn.commit()
print("Rows updated:", cur.rowcount)
conn.close()


