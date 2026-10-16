import pandas as pd

def repair_status_def(repair_SDT, repair_EDT, confirm_SDT):
    """
    Determine repair status based on date/time stamps.

    Args:
        repair_SDT: Repair Start Date/Time
        repair_EDT: Repair End Date/Time
        confirm_SDT: QC Confirm Start Date/Time
        confirm_EDT: QC Confirm End Date/Time

    Returns:
        str: Current status of the repair
    """


    # ✅ DEBUG: Print what we receive
    #print(f"DEBUG: repair_SDT={repair_SDT}, repair_EDT={repair_EDT}, confirm_SDT={confirm_SDT}")
    #print(f"DEBUG: Types: {type(repair_SDT)}, {type(repair_EDT)}, {type(confirm_SDT)}")
    

    # Step 1: Has repair started? (repair_SDT is NaN) 
    if pd.isna(repair_SDT):
        return "Pending Repair"
    
    # Step 2: Repair started but NOT ended? (repair_EDT is NaN)
    elif pd.isna(repair_EDT):
        return "Repair In Progress"
    
    # Step 3: Repair ended but QC NOT started? (confirm_SDT is NaN)
    elif pd.isna(confirm_SDT):
        return "Pending QC Confirm"
    
    # Step 4: All complete (all have values)
    else:
        return "QC Accepted"
    
   