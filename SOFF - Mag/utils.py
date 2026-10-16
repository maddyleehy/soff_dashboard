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



def repair_status(repair_SDT, repair_EDT, confirm_SDT, confirm_EDT):
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
    if repair_SDT == "":
        return "Pending Repair"
    elif repair_SDT !="" and repair_EDT == "":
        return "Repair In Progress"
    elif repair_EDT != "" and confirm_SDT == "":
        return "Pending QC Confirm"
    elif confirm_SDT != "" and confirm_EDT == "":
        return "QC Check In Progress"
    elif confirm_EDT != "":
        return confirm_EDT


     