import pandas as pd
from datetime import datetime, timezone

# =====================================
# TE1 Sorting Logic
# =====================================
def sort_by_te1(df, conn):
    master_te1 = df.read_sql(
        """
    SELECT body_no, seq_no
    FROM master_te1
    """,
    conn
    )
    df = df.merge(master_te1, on="body_no", how="left")
    df = df.sort_values(["last_updated", "seq_no"], ascending=[True, True])
    df = df.drop(columns=["seq_no"])
    return df


# =====================================
# Bucket Logic
# =====================================


def get_latest_bucket(conn): #takes the list of vehicles from bucket.csv added today
    return pd.read_sql(
    """
    SELECT *
    FROM bucket_history
    WHERE last_updated = (
    SELECT MAX(last_updated)
    FROM bucket_history
    )
    """,
    conn
)

def get_bucket_summary(bucket_df): #output of latest bucket combined with defects
     return (bucket_df
         .groupby("bucket")
         .size()
         .reset_index(name="vehicle_count")
         .sort_values("vehicle_count", ascending=False))


## =====================================
## Defect Logic
## =====================================

def get_defect_summary(conn, body_list): #repair count logic (num defect counts, repair started, repair completed, quality accepted) for all cars
    if not body_list:
        #return pd.DataFrame()
        return pd.DataFrame(columns=[
        "body_no", "defect_count", "pending_repair",
        "repair_in_progress", "pending_quality", "quality_accepted",
    ])
    placeholders = ",".join(["?"]*len(body_list)) #
    query = f"""
    SELECT
        body_no,

        COUNT(*) AS defect_count,

        
        SUM(
            CASE
                WHEN repair_start_dt IS NULL
                 OR repair_start_dt = ''
                THEN 1
                ELSE 0
            END
        ) AS pending_repair,

        SUM(
            CASE
                WHEN repair_start_dt IS NOT NULL
                 AND repair_start_dt <> ''
                 AND (repair_end_dt IS NULL OR repair_end_dt = '')       
                 AND confirm_yn = 'N'
                THEN 1
                ELSE 0
            END
        ) AS repair_in_progress,

        SUM(
            CASE
                WHEN repair_end_dt IS NOT NULL
                 AND repair_end_dt <> ''
                 AND confirm_yn = 'N'
                THEN 1
                ELSE 0
            END
        ) AS pending_quality, 

        SUM(
            CASE
                WHEN confirm_yn = 'Y'
                THEN 1
                ELSE 0
            END
        ) AS quality_accepted

    FROM defect_history

    WHERE last_updated = (
        SELECT MAX(last_updated)
        FROM defect_history
    )

    AND body_no IN ({placeholders})

    GROUP BY body_no
    """
    return pd.read_sql(query, conn, params=body_list)

def get_vehicle_status(row): #repair status logic per vehicle
    
    defect_count = row["defect_count"]
    pending_repair = row["pending_repair"]
    repair_in_progress = row["repair_in_progress"]
    pending_quality = row["pending_quality"]
    quality_accepted = row["quality_accepted"]

    if defect_count == 0:
        return "No Defects"

    elif repair_in_progress > 0:
        return "Repair In Progress"

    elif pending_quality > 0 :
        return "Quality Accepted"

    elif pending_quality + quality_accepted == defect_count:
        return "Repair Completed, Pending QC"

    elif pending_repair > 0:
        return "Pending Repair Start"

    else:
        return "Unknown"


     
# =====================================
# Summary Logic
# =====================================


def build_vehicle_summary(bucket_df, defect_summary): #combine bucket and defect count df
    vehicle_summary = bucket_df.merge(
        defect_summary,
        on="body_no",
        how="left"
    )

    metric_cols = [
        "defect_count",
        "pending_repair",
        "repair_in_progress",
        "pending_quality",
        "quality_accepted"
    ]

    for col in metric_cols:
        vehicle_summary[col] = (
            vehicle_summary[col]
            .fillna(0)
            .astype(int)
        )

    vehicle_summary["vehicle_status"] = vehicle_summary.apply(
        get_vehicle_status,
        axis=1
    )

    return vehicle_summary 



# =====================================
# Previous Status Logic
# =====================================


def previous_status(conn, row):
    body_no = row["body_no"]
    query = f"""
        WITH ranked AS (
            SELECT
                body_no,
                vehicle_status,
                ROW_NUMBER () OVER (
                    ORDER BY last_updated DESC 
                ) AS rn
                FROM dashboard_summary
                where body_no = ?
                )
            
            SELECT * from ranked where rn = 2 
            
        """
    
    df = pd.read_sql(query, conn, params=[body_no])
    if df.empty:
        return None
    return df.iloc[0]["vehicle_status"]

def get_previous_status(conn, row):
    return previous_status(conn, row)

# sample logic: all_vehicle_summary["last_status"] = all_vehicle_summary.apply(previous_status(conn, row))

# =====================================
# DT conversion
# =====================================

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

def to_db_datetime(value, date_only=False):
    """
    Convert a raw value to 'YYYY-MM-DD HH:MM:SS' (or 'YYYY-MM-DD' if date_only).
    Supports:
      - 14 digits  -> YYYYMMDDhhmmss   (e.g. 20261005142201)
      - 13 digits  -> epoch milliseconds, UTC (e.g. 1791880000000)
      - 8 digits   -> YYYYMMDD         (e.g. 20261005)
      - Text dates -> parsed by pandas (e.g. 2026-10-05 14:22:01)
    Returns None for blanks or unparseable values.
    """
    if pd.isna(value):
        return None

    s = str(value).strip()
    if s.endswith(".0"):            # Excel/float artifact: 20261005142201.0
        s = s[:-2]
    if s == "" or s.lower() in ("null", "nan", "none"):
        return None

    try:
        if s.isdigit():
            if len(s) == 14:
                dt = datetime.strptime(s, "%Y%m%d%H%M%S")
            elif len(s) == 13:
                dt = datetime.fromtimestamp(int(s) / 1000, tz=timezone.utc).replace(tzinfo=None)
            elif len(s) == 8:
                dt = datetime.strptime(s, "%Y%m%d")
            else:
                return None
        else:
            parsed = pd.to_datetime(s, errors="coerce")
            if pd.isna(parsed):
                return None
            dt = parsed.to_pydatetime()
    except ValueError:
        return None

    return dt.strftime(DATE_FORMAT if date_only else DATETIME_FORMAT)