
# =====================================
# troubleshooting
# =====================================

import sqlite3
import pandas as pd
from utils import get_status_changes

conn = sqlite3.connect("vehicle_history.db")

changes = get_status_changes(conn)

print("Columns:", changes.columns.tolist())
print("Rows:", len(changes))
print(changes.head(10).to_string())

if not changes.empty:
    print("\nChange counts:")
    print(changes["change"].value_counts(dropna=False))

conn.close()