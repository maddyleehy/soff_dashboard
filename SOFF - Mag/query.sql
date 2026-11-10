--WITH load_times AS (
--        SELECT DISTINCT last_updated
--        FROM defect_history
--        ORDER BY last_updated DESC
--        LIMIT 2
--    )
--    SELECT * 
--    FROM defect_history
--    WHERE last_updated IN (SELECT last_updated from load_times)




ORDER BY row_count DESC;


--select * from defect_history