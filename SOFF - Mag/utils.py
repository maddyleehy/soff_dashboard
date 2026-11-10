import pandas as pd
from datetime import datetime, timezone

# =====================================
# TE1 Sorting Logic
# =====================================
def sort_by_te1(df, conn):
    master_te1 = pd.read_sql(
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

def is_blank(value):
    return pd.isna(value) or str(value).strip() == ""

def get_defect_status(row): #repair status logic per defect

    fault_cd =  row["fault_cd"]
    repair_yn =  row["repair_yn"]
    repairer_id =  row["repairer_id"]
    repair_start_dt = row["repair_start_dt"]
    repair_end_dt = row["repair_end_dt"]
    confirm_yn = row["confirm_yn"]
    #confirm_dt = row["confirm_dt"]
    #confirmer_id =  row["confirmer_id"]

    if repairer_id == "A999999" and fault_cd == "F00137":
        return "Online Repairer - Record"

    elif repairer_id == "A999999" and fault_cd != "F00137":
        return "Online Repairer - Inline"
    
    elif repair_yn == "N" and is_blank(repair_start_dt) and is_blank(repair_end_dt):
        return "Pending Repair"

    elif repair_yn == "N" and not is_blank(repair_start_dt) and is_blank(repair_end_dt):
        return "Repair In Progress"

    elif repair_yn == "Y" and confirm_yn == "N":
        return "Repair Completed, Pending QC Confirm"

    elif repair_yn == "Y" and confirm_yn == "Y":
        return "QC Accepted"

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

#Previous status for latest dashboard summary
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

#Previous status for defect logic
def get_status_changes(conn):
    """Compare each defect's status between the latest load and the previous load."""
    df = pd.read_sql(
        """
        WITH load_times AS (
        SELECT DISTINCT last_updated
        FROM defect_history
        ORDER BY last_updated DESC
        LIMIT 2
    )
    SELECT * 
    FROM defect_history
    WHERE last_updated IN (SELECT last_updated from load_times)
    """,
    conn,
    )
    if df.empty:
        return df

    latest_ts = df["last_updated"].max()
    prev_ts = df.loc[df["last_updated"]< latest_ts, "last_updated"].max()

    # One row per unique_id in each load (keep the last if duplicates exist)
    current = (
        df[df["last_updated"] == latest_ts]
        .drop_duplicates("unique_id", keep = "last")
        [["file_name",          
          "body_no", 
          "fault_input_date",
          "stn_grp_nm", 
          "inspec_part_nm", 
          "defect_status",
          "unique_id"
          ]]
        .copy()
    )

    if pd.isna(prev_ts):
        current["prev_status"]= None
    else:
        previous = (
            df[df["last_updated"] == prev_ts]
            .drop_duplicates("unique_id", keep = "last")
            [["unique_id", "defect_status"]]
            .rename(columns = {"defect_status":"prev_defect_status"})
            
        )
        current = current.merge(previous, on="unique_id", how = "left")

    current ["change"] = current.apply(
        lambda r:"New" if pd.isna(r["prev_defect_status"])
        else ("Unchanged" if r["prev_defect_status"] == r["defect_status"] else "Changed"),
        axis = 1
    )

    current = current.rename(columns = {"defect_status" : "current_defect_status"})
   
    return current



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