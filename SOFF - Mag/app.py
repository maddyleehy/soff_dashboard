import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from db import load_csv_to_db, init_db

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

uploaded_file = st.file_uploader(
    "Upload CSV File",
    type=["csv"]
)

# Error Handling Load initial CSV
if uploaded_file is not None:
    try:
        rows_added = load_csv_to_db(uploaded_file)
        st.success(f"✅ Added {rows_added} rows into database")
    except Exception as e:
        st.exception(e)


st.write(
    pd.read_sql(
        "PRAGMA table_info(bucket_history)",
        conn
    )
)