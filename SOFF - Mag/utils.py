import pandas as pd

def get_bucket(loc):
        if loc == "PC010":
            return "PC-HC1"
        elif loc in ["HC010", "HC020", "HC030"]:
            return "HC1-HC3"
        elif loc in ["HC040", "HC050"]:
            return "HC4-HC5"
        elif loc in ["FC010", "FC020"]:
            return "FC1-FC2"
        else:
            return "QC Process"


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

def get_defect_summary(conn, body_list): #repair count logic (num defect counts, repair started, repair completed, quality accepted) for all cars
    if not body_list:
        return pd.DataFrame()
    placeholders = ",".join(["?"]*len(body_list))
    query = f"""
    SELECT
        body_no,

        COUNT(*) AS defect_count,

        SUM(
            CASE
                WHEN repair_start_dt IS NOT NULL
                 AND repair_start_dt <> ''
                THEN 1
                ELSE 0
            END
        ) AS repair_started,

        SUM(
            CASE
                WHEN repair_end_dt IS NOT NULL
                 AND repair_end_dt <> ''
                THEN 1
                ELSE 0
            END
        ) AS repair_completed,

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

    defects = row["defect_count"]
    started = row["repair_started"]
    completed = row["repair_completed"]
    accepted = row["quality_accepted"]

    if defects == 0:
        return "No Defects"

    elif started == 0:
        return "Repair Pending"

    elif accepted == defects:
        return "Quality Accepted"

    elif completed == defects:
        return "Repair Completed, Pending QC"

    else:
        return "Repair In Progress"


def build_vehicle_summary(bucket_df, defect_summary): #combine bucket and defect count df
    vehicle_summary = bucket_df.merge(
        defect_summary,
        on="body_no",
        how="left"
    )

    metric_cols = [
        "defect_count",
        "repair_started",
        "repair_completed",
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
# def repair_status(repair_SDT, repair_EDT, confirm_SDT, confirm_EDT):
#     """
#     Determine repair status based on date/time stamps.

#     Args:
#         repair_SDT: Repair Start Date/Time
#         repair_EDT: Repair End Date/Time
#         confirm_SDT: QC Confirm Start Date/Time
#         confirm_EDT: QC Confirm End Date/Time

#     Returns:
#         str: Current status of the repair
#     """
#     if repair_SDT == "":
#         return "Pending Repair"
#     elif repair_SDT !="" and repair_EDT == "":
#         return "Repair In Progress"
#     elif repair_EDT != "" and confirm_SDT == "":
#         return "Pending QC Confirm"
#     elif confirm_SDT != "" and confirm_EDT == "":
#         return "QC Check In Progress"
#     elif confirm_EDT != "":
#         return confirm_EDT


     