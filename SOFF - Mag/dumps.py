

import pandas as pd

#if search_body.strip():
#    search_text = search_body.strip().upper()
#    search_key = search_text.replace(" ", "")
#    pattern = f"%{search_key}%"
#
#    search_result = all_vehicle_summary[
#        all_vehicle_summary["body_no"]
#        .str.upper()
#        .str.replace(" ", "", regex=False)
#        .str.contains(search_key, regex=False, na=False)
#    ].drop(columns=["sub_bucket", "status", "id"], errors = "ignore")
#
#   # search_result = search_result.drop(columns=["sub_bucket", "status", "id"])
#
#    st.dataframe(
#        search_result,
#        column_order = ordered_columns (search_result),
#        width="stretch",
#        hide_index=True
#    )
#
#    # ===========================================
#    # Parts table
#    # ===========================================
#
#    pending_parts = pd.read_sql(
#        """SELECT * FROM parts_history AS p 
#        WHERE REPLACE(UPPER(p.body_no), ' ', '') LIKE ? 
#            and p.last_updated = (
#                SELECT MAX(x.last_updated) 
#                from parts_history as x 
#                where x.body_no = p.body_no
#            )
#        """,
#        conn,
#        params = [pattern]
#    )
#
#    pending_parts = pending_parts.drop(columns=["id","text"], errors = "ignore")
#
#    #script to return pending parts and parts supplied number
#    parts_status = pending_parts["status"].astype(str).str.strip().str.lower()
#    pending_count = int((parts_status == "open").sum())
#    supplied_count = int(parts_status.isin(["confirmed", "resolved"]).sum())
#
#    #st.subheader (f"Parts for {search_body.upper()} ({len(pending_parts)})")
#    st.subheader (f"Outstanding Parts")
#    st.write(f"**Pending parts:** {pending_count}")
#    st.write(f"**Parts supplied:** {supplied_count}")
#    
#
#    st.dataframe(
#        pending_parts,
#        column_order = ordered_columns(pending_parts),
#        width = "stretch",
#        hide_index = True
#    )
#
#    # ===========================================
#    # Defects table
#    # ===========================================
#    
#    defect_history = pd.read_sql(
#        """
#        select *
#        FROM defect_history as d
#        where replace (upper(d.body_no), ' ', '') like ?
#            and d.last_updated = (
#            select max(x.last_updated)
#            from defect_history as x
#            where x.body_no = d.body_no
#            )
#        """,
#        conn,
#        params = [pattern]
#    )
#
#    #script to return repair status
#    defect_status = defect_history["defect_status"].astype(str)
#    pending_repair_count = int((defect_status == "Pending Repair").sum()) 
#    repair_in_progress_count = int((defect_status == "Repair In Progress").sum()) 
#    pending_qc_count = int((defect_status == "Repair Completed, Pending QC Confirm").sum())
#    repair_completed_count = int(defect_status.isin(["Online Repairer", "QC Accepted"]).sum())
#   
#    #st.subheader (f"Defect for {search_body.upper()} ({len(defect_history)})")
#    st.subheader (f"All Defects")
#    st.write(f"**Pending Repair:** {pending_repair_count}")
#    st.write(f"**Repair In Progress:** {repair_in_progress_count}")
#    st.write(f"**Pending QC Confirm:** {pending_qc_count}")
#    #st.write(f"**Repair Completed:** {repair_completed_count}")
#    
#      
#    st.dataframe(
#        defect_history,
#        column_order = ordered_columns(defect_history),
#        width = "stretch",
#        hide_index = True
#        )
#



pd.read_sql(
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
    """)