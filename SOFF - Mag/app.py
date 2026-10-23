import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from db import (
    load_bucket_csv_to_db, 
    load_defect_csv_to_db, 
    load_parts_csv_to_db, 
    load_dashboard_summary_to_db, 
    init_db,)
from utils import (get_latest_bucket, get_bucket_summary, get_defect_summary, get_vehicle_status, build_vehicle_summary)

#Load once helper function

def load_once(uploaded_file, key, loader, label):
    """Load an uploaded file only once, not on every Streamlit rerun."""
    if uploaded_file is None:
        return

    file_id = f"{uploaded_file.name}-{uploaded_file.size}"

    if st.session_state.get(f"{key}_loaded") != file_id:
        uploaded_file.seek(0)              # reset read position before parsing
        rows = loader(uploaded_file)
        st.session_state[f"{key}_loaded"] = file_id
        st.session_state[f"{key}_rows"] = rows

    st.success(f"{label}: {st.session_state[f'{key}_rows']} rows loaded from {uploaded_file.name}")


init_db() #initialize db, creates table function from db.py

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

# Bucket status
st.subheader("Bucket Status Upload")
bucket_file = st.file_uploader("Upload Bucket CSV", type=["csv"], key="bucket")
load_once(bucket_file, "bucket", load_bucket_csv_to_db, "Bucket")

# Defect status
st.subheader("Defect Status Upload")
defect_file = st.file_uploader("Upload Defect CSV", type=["csv"], key="defect")
load_once(defect_file, "defect", load_defect_csv_to_db, "Defect")

#Parts status
st.subheader("Parts ETA Upload")
parts_file = st.file_uploader("Upload Parts CSV", type=["csv"], key="parts")
load_once(parts_file, "parts", load_parts_csv_to_db, "Parts")

# ===========================================
# Historical count for bucket, defect, parts
# ===========================================

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
parts_count = pd.read_sql(
    "SELECT COUNT(*) AS cnt " \
    "FROM parts_history", 
    conn)

st.metric("Parts Records", int(parts_count.iloc[0]["cnt"]))

col1, col2, col3 = st.columns(3)
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
with col3:
    st.metric(
        "Parts Records",
        int(parts_count.iloc[0]["cnt"])
    )   

# ===========================================
# ===========================================


latest_bucket_df = get_latest_bucket(conn)

# Defect Count Logic
all_wip_list = latest_bucket_df["body_no"].unique().tolist() #list of unsigned off vehicles


all_defect_summary = get_defect_summary(conn, all_wip_list) #defect count logic for unsigned off vehicles
all_vehicle_summary = build_vehicle_summary(latest_bucket_df, all_defect_summary) #bucket and defect count for unsigned off vehicles


    
# ===========================================
# Vehicle Buckets UI
# ===========================================

st.header("Vehicle Buckets")

bucket_summary = get_bucket_summary(latest_bucket_df)
st.subheader("Vehicle Buckets") # Selected Bucket and display list of vehicles under it

if bucket_summary.empty:
    st.warning("No bucket data available.")
    st.stop()
cols = st.columns(len(bucket_summary))

bucket_order = ["PC-HC1","HC1-HC3","INITIAL","HC4-HC5","FC1-FC2", "ROAD, BSR, WATER", "FINAL", "REPAIR"]
# Reorder dataframe
bucket_summary = (
    bucket_summary.set_index("bucket").reindex(bucket_order).reset_index()
)
for i, row in enumerate(bucket_summary.itertuples()): 
    with cols[i]:
        if st.button(
            f"{row.bucket}\n({row.vehicle_count})",
            use_container_width=True,
            key=row.bucket
        ):
            st.session_state["selected_bucket"] = row.bucket

# ===========================================
# Vehicle in "Selected Bucket" UI
# ===========================================

selected_bucket = st.session_state.get(
    "selected_bucket",
    bucket_summary.iloc[0]["bucket"]
)
st.write(f"Selected Bucket: {selected_bucket}")
bucket_vehicles_df = latest_bucket_df[
    latest_bucket_df["bucket"] == selected_bucket
]
#print(latest_bucket_df)

st.subheader(f"Vehicles in {selected_bucket}")

st.dataframe(
    bucket_vehicles_df[
        [
            "body_no",
            "sub_bucket_nm",
            "status_nm"
            #"parts_ETA"
        ]
    ],
    width="stretch",
    hide_index=True
)

# ===========================================
# Load Dashboard to DB script
# ===========================================

if st.button("Load Database Snapshot", type="primary"):
    dashboard_summary = all_vehicle_summary.copy()
    dashboard_summary["snapshot_dt"] = datetime.now()
    load_dashboard_summary_to_db(dashboard_summary)
    st.success(
        f"Loaded {len(dashboard_summary)} rows"
    )

# Specific Bucket Defect
vehicle_summary = all_vehicle_summary[all_vehicle_summary["bucket"]==selected_bucket]


# ===========================================
# Latest Dashboard Summary UI
# ===========================================

st.subheader("Latest Dashboard Summary")
st.dataframe(
    all_vehicle_summary,
    width="stretch",
    hide_index=True
)


# ===========================================
# Search Vehicle
# ===========================================


st.subheader("Search Vehicle") 
search_body = st.text_input(
    "Enter Body No",
    placeholder="e.g. ABC123"
)

if search_body:
    search_result = all_vehicle_summary[
        all_vehicle_summary["body_no"]
        .str.contains(search_body, case=False, na=False)
    ]

    st.dataframe(
        search_result,
        width="stretch",
        hide_index=True
    )

    pending_parts = pd.read_sql(
        "SELECT * FROM parts_history WHERE body_no = ? and last_updated = (SELECT MAX(last_updated) from parts_history where body_no = ?)",
        conn,
        params = [search_body, search_body]
    )

    st.subheader (f"Parts for {search_body}")
    st.dataframe(
        pending_parts,
        width = "stretch",
        hide_index = True
    )

    defect_history = pd.read_sql(
        """
        SELECT body_no, fault_input_date, repair_yn, repair_start_dt,repair_end_dt, repairer_id, confirm_yn, confirm_dt, confirmer_id, last_updated
        FROM defect_history 
        WHERE body_no = ? and last_updated = (SELECT MAX (last_updated) from defect_history where body_no = ?)""",
        conn,
        params = [search_body, search_body]
    )

    st.subheader (f"Defect for {search_body}")
    st.dataframe(
        defect_history,
        width = "stretch",
        hide_index = True
        )



# ===========================================
# Bucket History Table UI
# ===========================================
#st.subheader("Bucket History Table")
#bucket_df = pd.read_sql(
#    """
#    SELECT *
#    FROM bucket_history
#    ORDER BY last_updated DESC
#    LIMIT 100
#    """,
#    conn
#)
#st.dataframe(
#    bucket_df,
#    use_container_width=True,
#    hide_index=True
#)


# ===========================================
# Defect History Table UI
# ===========================================
#st.subheader("Defect History Table")
#defect_df = pd.read_sql(
#    """
#    SELECT *
#    FROM defect_history
#    ORDER BY last_updated DESC
#    LIMIT 100
#    """,
#    conn
#)
#
#st.dataframe(
#    defect_df,
#    use_container_width=True,
#    hide_index=True
#)
#
#cursor = conn.cursor()
#
