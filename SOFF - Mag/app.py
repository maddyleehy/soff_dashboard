import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from db import (load_bucket_csv_to_db, load_defect_csv_to_db, load_dashboard_summary_to_db, init_db)
init_db()

# =====================================
# PAGE SETTINGS
# =====================================

st.set_page_config(
    page_title="Vehicle Tracking Dashboard",
    layout="wide"
)

st.title("Unsigned-Off Vehicle Dashboard")
@st.cache_resource


def get_db_connection():
    return sqlite3.connect(
        "vehicle_history.db",
        check_same_thread=False
    )

conn = get_db_connection()


# =====================================
# CSV uploading
# =====================================

# Load initial CSV

st.subheader("Bucket Status Upload")

bucket_file = st.file_uploader(
    "Upload Bucket CSV",
    type=["csv"],
    key="bucket"
)

if bucket_file:
    rows_added = load_bucket_csv_to_db(bucket_file)
    st.success(f"Added {rows_added} bucket rows")


st.subheader("Defect Status Upload")

defect_file = st.file_uploader(
    "Upload Defect CSV",
    type=["csv"],
    key="defect"
)

if defect_file:
    rows_added = load_defect_csv_to_db(defect_file)
    st.success(f"Added {rows_added} defect rows")

#
bucket_count = pd.read_sql(
    """
    SELECT COUNT(*) AS cnt
    FROM bucket_history
    """,
    conn
)

defect_count = pd.read_sql(
    """
    SELECT COUNT(*) AS cnt
    FROM defect_history
    """,
    conn
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Bucket Records",
        int(bucket_count.iloc[0]["cnt"])
    )

with col2:
    st.metric(
        "Defect Records",
        int(defect_count.iloc[0]["cnt"])
    )

# Bucket UI
latest_bucket_df = pd.read_sql(
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

st.header("Vehicle Buckets")

bucket_summary = (
    latest_bucket_df
    .groupby("bucket")
    .size()
    .reset_index(name="vehicle_count")
    .sort_values("vehicle_count", ascending=False)
)

# st.dataframe(
#     bucket_summary,
#     width="stretch",
#     hide_index=True
# )

# Selected Bucket and display list of vehicles under it
st.subheader("Vehicle Buckets")

cols = st.columns(len(bucket_summary))

for i, row in enumerate(bucket_summary.itertuples()):

    with cols[i]:

        if st.button(
            f"{row.bucket}\n({row.vehicle_count})",
            use_container_width=True,
            key=row.bucket
        ):
            st.session_state["selected_bucket"] = row.bucket

selected_bucket = st.session_state.get(
    "selected_bucket",
    bucket_summary.iloc[0]["bucket"]
)
st.write(f"Selected Bucket: {selected_bucket}")
bucket_vehicles_df = latest_bucket_df[
    latest_bucket_df["bucket"] == selected_bucket
]

st.subheader(f"Vehicles in {selected_bucket}")

st.dataframe(
    bucket_vehicles_df[
        [
            "body_no",
            "sub_bucket",
            "status"
        ]
    ],
    width="stretch",
    hide_index=True
)

# Defect Count Logic

all_wip_list = latest_bucket_df["body_no"].unique().tolist()
placeholders = ",".join(["?"] * len(all_wip_list))
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
# defect_summary = pd.read_sql(
#     query,
#     conn,
#     params=all_wip_list
# ) 
# Dashboard Summary for cars in all buckets


all_defect_summary = pd.read_sql(query, conn, params=all_wip_list)
all_vehicle_summary = latest_bucket_df.merge(all_defect_summary, on="body_no", how="left")

for col in ["defect_count", "repair_started", "repair_completed", "quality_accepted"]:
    all_vehicle_summary[col] = (all_vehicle_summary[col].fillna(0).astype(int))

def get_vehicle_status(row):

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

all_vehicle_summary["vehicle_status"] = all_vehicle_summary.apply(get_vehicle_status, axis=1)
# Load Dashboard to DB Button
if st.button("Load Database Snapshot", type="primary"):
    dashboard_summary = all_vehicle_summary.copy()
    dashboard_summary["snapshot_dt"] = datetime.now()
    load_dashboard_summary_to_db(dashboard_summary)
    st.success(
        f"Loaded {len(dashboard_summary)} rows"
    )

# Specific Bucket Defect
vehicle_summary = all_vehicle_summary[all_vehicle_summary["bucket"]==selected_bucket]

st.subheader("Defect Summary")

st.dataframe(
    vehicle_summary,
    width="stretch",
    hide_index=True
)

# Display Bucket History Table

st.subheader("Bucket History Table")
bucket_df = pd.read_sql(
    """
    SELECT *
    FROM bucket_history
    ORDER BY last_updated DESC
    LIMIT 100
    """,
    conn
)
st.dataframe(
    bucket_df,
    use_container_width=True,
    hide_index=True
)

# Display Defect History Table
st.subheader("Defect History Table")
defect_df = pd.read_sql(
    """
    SELECT *
    FROM defect_history
    ORDER BY last_updated DESC
    LIMIT 100
    """,
    conn
)

st.dataframe(
    defect_df,
    use_container_width=True,
    hide_index=True
)

cursor = conn.cursor()


#st.success("defect_history deleted")