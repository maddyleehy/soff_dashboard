import pandas as pd

# =====================================
# Bucket Logic
# =====================================

#def get_bucket(loc):
#        if loc == "PC010":
#            return "PC-HC1"
#        elif loc in ["HC010", "HC020", "HC030"]:
#            return "HC1-HC3"
#        elif loc in ["HC040", "HC050"]:
#            return "HC4-HC5"
#        elif loc in ["FC010", "FC020"]:
#            return "FC1-FC2"
#        else:
#            return "QC Process"


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


# =====================================
# Defect Logic
# =====================================

def get_defect_summary(conn, body_list): #repair count logic (num defect counts, repair started, repair completed, quality accepted) for all cars
    if not body_list:
        return pd.DataFrame()
    placeholders = ",".join(["?"]*len(body_list)) #
    query = f"""
    SELECT
        body_no,

        COUNT(*) AS defect_count,

        SUM(
            CASE
                WHEN repair_start_dt IS NULL
                 AND repair_start_dt = ''
                THEN 1
                ELSE 0
            END
        ) AS pending_repair,

        SUM(
            CASE
                WHEN repair_start_dt IS NOT NULL
                 AND repair_start_dt <> ''
                 AND repair_end_dt IS NULL
                 AND repair_end_dt = ''
                THEN 1
                ELSE 0
            END
        ) AS repair_in_progress,

        SUM(
            CASE
                WHEN repair_end_dt IS NOT NULL
                 AND repair_end_dt <> ''
                 and confirm_yn = 'N'
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

    defects = row["defect_count"]
    #pending_repair = row["pending_repair"]
    repair_in_progress = row["repair_in_progress"]
    pending_quality = row["pending_quality"]
    quality_accepted = row["quality_accepted"]

    if defects == 0:
        return "No Defects"

    elif repair_in_progress > 0:
        return "Repair In Progress"

    elif pending_quality > 0 :
        return "Quality Accepted"

    elif pending_quality + quality_accepted == defects:
        return "Repair Completed, Pending QC"

    else:
        return "Pending Repair"


     
# =====================================
# Parts Logic
# =====================================

#def get_parts_eta_status(row):
#    body_num = row["body_no"]
#    query = f"""
#    select max(eta) from parts_history
#    where body_no = body_num
#    
#"""
#    return pd.read_sql(query, conn, params=body_list)


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

 #   vehicle_summary["parts_eta_status"] = vehicle_summary.apply(
 #       get_parts_eta_status,
 #       axis=1
 #       )

    return vehicle_summary 


     
