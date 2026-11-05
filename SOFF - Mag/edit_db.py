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
import os
os.remove("vehicle_history.db")
print("Deleted vehicle_history.db")