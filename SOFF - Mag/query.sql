WITH load_times AS (
        SELECT DISTINCT file_name
        FROM defect_history
        ORDER BY file_name DESC
        LIMIT 2
    )
    SELECT DISTINCT file_name 
    FROM defect_history
    WHERE file_name IN (SELECT file_name from load_times)




--ORDER BY row_count DESC;


--select * from defect_history