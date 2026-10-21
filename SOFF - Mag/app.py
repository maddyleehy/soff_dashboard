import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from db import (load_bucket_csv_to_db, load_repair_csv_to_db, init_db)
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


st.subheader("Repair Status Upload")

repair_file = st.file_uploader(
    "Upload Repair CSV",
    type=["csv"],
    key="repair"
)

if repair_file:
    rows_added = load_repair_csv_to_db(repair_file)
    st.success(f"Added {rows_added} repair rows")

#
bucket_count = pd.read_sql(
    """
    SELECT COUNT(*) AS cnt
    FROM bucket_history
    """,
    conn
)

repair_count = pd.read_sql(
    """
    SELECT COUNT(*) AS cnt
    FROM repair_history
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
        "Repair Records",
        int(repair_count.iloc[0]["cnt"])
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

# Display Repair History Table
st.subheader("Repair History Table")
repair_df = pd.read_sql(
    """
    SELECT *
    FROM repair_history
    ORDER BY last_updated DESC
    LIMIT 100
    """,
    conn
)

st.dataframe(
    repair_df,
    use_container_width=True,
    hide_index=True
)

cursor = conn.cursor()


st.success("repair_history deleted")