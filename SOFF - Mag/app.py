import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from db import (
    load_bucket_csv_to_db, 
    load_defect_csv_to_db, 
    load_parts_csv_to_db, 
    load_dashboard_summary_to_db, 
    init_db,load_te1_master_to_db)
from utils import (get_latest_bucket, get_bucket_summary, get_defect_summary, get_vehicle_status, 
                   build_vehicle_summary, previous_status, get_previous_status, get_status_changes, get_part_summary)


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
#st.write(
#    pd.read_sql(
#        """
#        SELECT names
#        FROM sqlite_master
#        WHERE type='table'
#        ORDER BY name
#        """,
#        conn
#    )
#)

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

#TE1_Master
st.subheader("TE1 Master Upload")
te1_file = st.file_uploader("Upload TE1 Master CSV",
    type=["csv"],
    key="te1")
load_once(te1_file, "te1", load_te1_master_to_db, "TE1 Master")


# ===========================================
# ===========================================


latest_bucket_df = get_latest_bucket(conn)
#latest_bucket_df["parts_status"] = df.apply

# Defect Count Logic
all_wip_list = latest_bucket_df["body_no"].unique().tolist() #list of unsigned off vehicles

all_defect_summary = get_defect_summary(conn, all_wip_list) #defect count logic for unsigned off vehicles

all_vehicle_summary = build_vehicle_summary(latest_bucket_df, all_defect_summary) #bucket and defect count for unsigned off vehicles

all_part_summary = get_part_summary(conn, all_wip_list)

all_vehicle_summary = all_vehicle_summary.merge(all_part_summary, on="body_no", how="left")

st.dataframe(all_vehicle_summary)
    
# ===========================================
# Vehicle Buckets UI
# ===========================================

st.header("Vehicle Buckets")

bucket_summary = get_bucket_summary(latest_bucket_df)
st.subheader("Vehicle Buckets") # Selected Bucket and display list of vehicles under it

if bucket_summary.empty:
    st.warning("No bucket data available.")
    st.stop()

bucket_order = ["PC-HC1","HC1-HC3","INITIAL","HC4-HC5","FC1-FC2", "ROAD, BSR, WATER", "FINAL", "REPAIR"]

bucket_summary["bucket_order"] = pd.Categorical(
    bucket_summary["bucket"], categories=bucket_order, ordered=True
)
bucket_summary = (
    bucket_summary.sort_values("bucket_order")
    .drop(columns="bucket_order")
    .reset_index(drop=True)
)

cols = st.columns(len(bucket_summary))


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
bucket_vehicles_df = bucket_vehicles_df.merge(all_vehicle_summary[["body_no","prod_part_status","repair_part_status"]],
                    on="body_no", how="left")
#print(latest_bucket_df)
if selected_bucket == "PC-HC1":
    bucket_vehicles_df["part_status"] = bucket_vehicles_df["prod_part_status"]
else:
    bucket_vehicles_df["part_status"] = bucket_vehicles_df["repair_part_status"]

st.subheader(f"Vehicles in {selected_bucket}")

st.dataframe(
    bucket_vehicles_df[
        [
            "body_no",
            "sub_bucket_nm",
            "status_nm",
            "part_status"
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
# Changes Table
# ===========================================

changes = get_status_changes (conn)
summary = (
    changes[changes["change"].isin(["Changed", "New"])]
    .groupby(["body_no", "change"])
    .size()
    .unstack(fill_value = 0)
    .reindex(columns = ["Changed", "New"], fill_value = 0)
    .rename(columns={"Changed":"change_count", "New": "new_count"})
    .rename_axis(columns=None)
    .reset_index()
    .sort_values("change_count", ascending = False)
)

changes_qty = changes[changes["change"].isin(["Changed"])].groupby(["body_no"])
new_qty = changes[changes["change"].isin(["New"])].groupby(["body_no"])

st.subheader(f"Body Numbers with Status Changes ({len(summary)})")
st.write(f"**Body Number with changes:** {len(changes_qty)}")
st.write(f"**Body Number with new defects:** {len(new_qty)}")


if summary.empty: #summary -> change_summary
    st.info ("No status changes between the latest and previous load.")
else:
    st.dataframe(
        #change_summary,
        summary,
        width = "stretch", 
        hide_index = True)

changes_view = changes.loc[
    (changes["change"] != "Unchanged") & (changes["current_defect_status"] != "Online Repairer - Record"),
    ["change",
     "file_name",
     "body_no",
     "fault_input_date",
     "stn_grp_nm",
     "inspec_part_nm",
     "current_defect_status",
     "prev_defect_status",
     "unique_id"
     ],
]

#st.subheader(f"Defect Status Changes ({len(changes_view)})")
#st.dataframe(
#    changes_view,    
#    width="stretch",
#    hide_index=True,
#)


# ===========================================
# Default column order helper
# ===========================================
default_column_order = [
    "id",
    "change",
    "body_no",
    "current_defect_status",
    "prev_defect_status",
    "bucket",
    "vehicle_status",
    "last_status",
    "part_no",
    "part_name",
    "eta",
    "status",
    "defect_status",
    "fault_input_date",
    "stn_nm",
    "inspec_part_nm", 
    "fault_nm", 
    "repair_yn",
    "repairer_nm",
    "repair_start_dt",
    "repair_end_dt",
    "confirm_yn",
    "confirmer_nm",
    "confirm_dt",
    "last_updated",
]


def ordered_columns (df, preferred = default_column_order):
    first = [c for c in preferred if c in df.columns]
    rest = [c for c in df.columns if c not in first]
    return first + rest

# ===========================================
# Latest Dashboard Summary UI
# ===========================================


#st.subheader("Latest Dashboard Summary")

#latest_dashboard = all_vehicle_summary.copy()
#latest_dashboard = latest_dashboard.drop(columns=["sub_bucket", "status"]) 
#latest_dashboard["last_status"] = latest_dashboard.apply(lambda row: get_previous_status(conn, row), axis=1)
#
#st.dataframe(
#    latest_dashboard,
#    column_order = ordered_columns(latest_dashboard),
#    width="stretch",
#    hide_index=True
#)


# ===========================================
# Search Vehicle
# ===========================================

st.subheader("Search Vehicle") 
search_body = st.text_input(
    "Enter Body No",
    placeholder="e.g. ABC123"
)

if search_body:
    search_text = "".join(search_body.split())

    search_result = all_vehicle_summary[
        all_vehicle_summary["body_no"]
        .astype(str)
        .str.replace(r"\s+", "", regex=True)
        .str.contains(search_text, case=False, na=False)
    ]

    search_result = search_result.drop(columns=["sub_bucket", "status"])

    if not search_result.empty:
        actual_body_no = search_result.iloc[0]["body_no"]
    #st.dataframe(
    #    search_result,
    #    column_order = ordered_columns (search_result),
    #    width="stretch",
    #    hide_index=True
    #)


    # ===========================================
    # Defects table
    # ===========================================
    
    defect_history = pd.read_sql(
        """
        SELECT body_no, fault_input_date, repair_yn, repair_start_dt,repair_end_dt, repairer_nm, confirm_yn, confirm_dt, confirmer_nm, last_updated, defect_status, unique_id, inspec_part_nm, fault_nm, stn_nm
        FROM defect_history 
        WHERE (body_no) = ? and last_updated = (SELECT MAX (last_updated) from defect_history where (body_no) = ?)
        ORDER BY
        CASE defect_status
        WHEN 'Repair In Progress' THEN 0
        WHEN 'Pending Repair' THEN 1
        WHEN 'Repair Completed, Pending QC Confirm' THEN 2
        WHEN 'QC Accepted' THEN 3
        WHEN 'Online Repairer - Inline' THEN 4
        ELSE 5
        END

        """,
        conn,
        params = [actual_body_no, actual_body_no]
    )

    repair_status = defect_history["defect_status"].astype(str).str.lower()
    pending_repair_count = int((repair_status == "pending repair").sum())
    repair_in_progress_count = int((repair_status == "repair in progress").sum())
    pending_qc_count = int((repair_status == "repair completed, pending qc confirm").sum())

   
    st.subheader (f"Defect for {actual_body_no} ({len(defect_history)})")
    st.write(f"**Pending Repair:** {pending_repair_count}")
    st.write(f"**Repair In Progress:** {repair_in_progress_count}")
    st.write(f"**Repair Completed, Pending QC Confirm:** {pending_qc_count}")

    status_cols = changes[["unique_id", "current_defect_status", "prev_defect_status", "change"]]
    defect_view = defect_history.merge(status_cols, on ="unique_id", how = "left").drop(columns = ["body_no", "defect_status"])
    defect_view ["change"] = defect_view ["change"].fillna("No Prior Load")

    st.dataframe(
        #defect_history,
        #column_order = ordered_columns(defect_history),
        defect_view, 
        column_order = ordered_columns(defect_view),
        width = "stretch",
        hide_index = True
        )


    # ===========================================
    # Parts table
    # ===========================================
    pending_parts = pd.read_sql(
        "SELECT * FROM parts_history WHERE (body_no) = ? and last_updated = (SELECT MAX(last_updated) from parts_history where (body_no) = ?)",
        conn,
        params=[actual_body_no, actual_body_no]
    )

    pending_parts = pending_parts.drop(columns=["body_no", "id","text"], errors = "ignore")

    #script to return pending parts and parts supplied number
    parts_status = pending_parts["status"].astype(str).str.strip().str.lower()
    pending_count = int((parts_status == "open").sum())
    supplied_count = int(parts_status.isin(["confirmed", "resolved"]).sum())

    st.subheader (f"Parts for {actual_body_no} ({len(pending_parts)})")
    st.write(f"**Pending parts:** {pending_count}")
    st.write(f"**Parts supplied:** {supplied_count}")

    st.dataframe(
        pending_parts,
        column_order = ordered_columns(pending_parts),
        width = "stretch",
        hide_index = True
    )




# ===========================================
# Repair Status
# ===========================================
# ===========================================
# Latest Repair Status (most recent non-null value per field)
# ===========================================
latest_repair = pd.read_sql("""
    SELECT
        b.body_no,
        (
            SELECT r.major_minor
            FROM repair_status r
            WHERE r.body_no = b.body_no
              AND r.major_minor IS NOT NULL
              AND LOWER(TRIM(r.major_minor)) NOT IN ('', 'none')
            ORDER BY r.last_updated DESC, r.rowid DESC
            LIMIT 1
        ) AS major_minor,
        (
            SELECT r.remarks
            FROM repair_status r
            WHERE r.body_no = b.body_no
              AND r.remarks IS NOT NULL
              AND LOWER(TRIM(r.remarks)) NOT IN ('', 'none')
            ORDER BY r.last_updated DESC, r.rowid DESC
            LIMIT 1
        ) AS remarks
    FROM (SELECT DISTINCT body_no FROM repair_status) b
""", conn)

repair_df = (
    latest_bucket_df[["body_no"]]
    .drop_duplicates()
    .merge(latest_repair, on="body_no", how="left")
)
repair_df["major_minor"] = repair_df["major_minor"].fillna("None")
repair_df["remarks"] = repair_df["remarks"].fillna("None")

edited_df = st.data_editor(
    repair_df,
    column_config={
        "major_minor": st.column_config.SelectboxColumn(
            "Major/Minor",
            options=["None", "Major", "Minor"]
        ),
        "remarks": st.column_config.TextColumn("Remarks")
    },
    disabled=["body_no"],
    hide_index=True,
    width="stretch"
)

# ===========================================
# Save Repair Status to DB
# ===========================================
def clean_value(series):
    """Strip whitespace and turn blank / 'None' into NULL (None)."""
    s = series.fillna("").astype(str).str.strip()
    return s.where(~s.str.lower().isin(["", "none"]), None)

if st.button("Save Repair Status"):
    new_df = pd.DataFrame({
        "body_no": edited_df["body_no"].values,
        "major_minor": clean_value(edited_df["major_minor"]).values,
        "remarks": clean_value(edited_df["remarks"]).values,
    })
    old_major = clean_value(repair_df["major_minor"]).values
    old_remarks = clean_value(repair_df["remarks"]).values

    # A row is changed if either field differs from what is displayed
    changed = (
        (pd.Series(new_df["major_minor"].values).fillna("").values != pd.Series(old_major).fillna("").values) |
        (pd.Series(new_df["remarks"].values).fillna("").values != pd.Series(old_remarks).fillna("").values)
    )

    # Save if at least one field has a real value (either field alone is enough)
    has_value = new_df["major_minor"].notna() | new_df["remarks"].notna()

    save_df = new_df.loc[changed & has_value].copy()

    if save_df.empty:
        st.warning("No changes with a real value to save.")
    else:
        save_df["last_updated"] = datetime.now()
        save_df.to_sql(
            "repair_status",
            conn,
            if_exists="append",
            index=False
        )
        st.success(f"Saved {len(save_df)} repair records.")



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

