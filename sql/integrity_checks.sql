-- =============================================================================
-- SQL Integrity Checks & Relational Assertions
-- AtliQ Motors EV Insights Pipeline
-- Reference: architecture.md §7, memory.md "What NOT to re-derive from scratch"
-- =============================================================================

-- 1. Table Row Counts Check
-- Expected: dim_date = 36, dim_revenue = 2, makers = 816, state = 2445
SELECT 'dim_date' AS table_name, COUNT(*) AS row_count, 36 AS expected_count FROM dim_date
UNION ALL
SELECT 'dim_revenue', COUNT(*), 2 FROM dim_revenue
UNION ALL
SELECT 'electric_vehicle_sales_by_makers', COUNT(*), 816 FROM electric_vehicle_sales_by_makers
UNION ALL
SELECT 'electric_vehicle_sales_by_state', COUNT(*), 2445 FROM electric_vehicle_sales_by_state;

-- 2. Foreign Key Orphan Check
-- Expected: 0 orphans across all foreign key relationships
SELECT 'makers_orphan_dates' AS check_name, COUNT(*) AS orphan_count
FROM electric_vehicle_sales_by_makers m
LEFT JOIN dim_date d ON m.date = d.date
WHERE d.date IS NULL
UNION ALL
SELECT 'state_orphan_dates', COUNT(*)
FROM electric_vehicle_sales_by_state s
LEFT JOIN dim_date d ON s.date = d.date
WHERE d.date IS NULL
UNION ALL
SELECT 'makers_orphan_categories', COUNT(*)
FROM electric_vehicle_sales_by_makers m
LEFT JOIN dim_revenue r ON m.vehicle_category = r.vehicle_category
WHERE r.vehicle_category IS NULL
UNION ALL
SELECT 'state_orphan_categories', COUNT(*)
FROM electric_vehicle_sales_by_state s
LEFT JOIN dim_revenue r ON s.vehicle_category = r.vehicle_category
WHERE r.vehicle_category IS NULL;

-- 3. Total EV Sales Cross-Table Reconciliation
-- Expected: Makers Total EV Sales == State Total EV Sales == 2,066,111
WITH totals AS (
    SELECT 
        (SELECT SUM(electric_vehicles_sold) FROM electric_vehicle_sales_by_makers) AS makers_ev_total,
        (SELECT SUM(electric_vehicles_sold) FROM electric_vehicle_sales_by_state) AS state_ev_total
)
SELECT 
    makers_ev_total, 
    state_ev_total,
    (makers_ev_total - state_ev_total) AS difference,
    CASE WHEN makers_ev_total = 2066111 AND state_ev_total = 2066111 THEN 'PASS' ELSE 'FAIL' END AS assertion_status
FROM totals;

-- 4. Vehicle Category Breakdown Validation
-- Expected: 2-Wheelers = 1,913,168; 4-Wheelers = 152,943
SELECT 
    vehicle_category,
    SUM(electric_vehicles_sold) AS actual_units,
    CASE 
        WHEN vehicle_category = '2-Wheelers' AND SUM(electric_vehicles_sold) = 1913168 THEN 'PASS'
        WHEN vehicle_category = '4-Wheelers' AND SUM(electric_vehicles_sold) = 152943 THEN 'PASS'
        ELSE 'FAIL'
    END AS assertion_status
FROM electric_vehicle_sales_by_makers
GROUP BY vehicle_category;

-- 5. Headline Penetration Rate Validation
-- Expected: Penetration Rate = 3.61%
SELECT 
    SUM(electric_vehicles_sold) AS total_ev_sold,
    SUM(total_vehicles_sold) AS total_vehicles_sold,
    ROUND(SUM(electric_vehicles_sold)::NUMERIC / SUM(total_vehicles_sold) * 100, 2) AS penetration_rate_pct,
    CASE 
        WHEN ROUND(SUM(electric_vehicles_sold)::NUMERIC / SUM(total_vehicles_sold) * 100, 2) = 3.61 THEN 'PASS'
        ELSE 'FAIL'
    END AS assertion_status
FROM electric_vehicle_sales_by_state;

-- 6. EV Sales CAGR (FY2022 to FY2024) Validation
-- Expected: 93.91%
WITH cagr_calc AS (
    SELECT 
        SUM(CASE WHEN d.fiscal_year = 2022 THEN m.electric_vehicles_sold ELSE 0 END) AS ev_2022,
        SUM(CASE WHEN d.fiscal_year = 2024 THEN m.electric_vehicles_sold ELSE 0 END) AS ev_2024
    FROM electric_vehicle_sales_by_makers m
    JOIN dim_date d ON m.date = d.date
)
SELECT 
    ev_2022,
    ev_2024,
    ROUND((( (ev_2024::FLOAT / ev_2022) ^ 0.5 ) - 1) * 100, 2) AS ev_cagr_pct,
    CASE 
        WHEN ROUND((( (ev_2024::FLOAT / ev_2022) ^ 0.5 ) - 1) * 100, 2) = 93.91 THEN 'PASS'
        ELSE 'FAIL'
    END AS assertion_status
FROM cagr_calc;

-- 7. Total Vehicles Sold CAGR (FY2022 to FY2024) Validation
-- Expected: 13.56%
WITH state_cagr AS (
    SELECT 
        SUM(CASE WHEN d.fiscal_year = 2022 THEN s.total_vehicles_sold ELSE 0 END) AS total_2022,
        SUM(CASE WHEN d.fiscal_year = 2024 THEN s.total_vehicles_sold ELSE 0 END) AS total_2024
    FROM electric_vehicle_sales_by_state s
    JOIN dim_date d ON s.date = d.date
)
SELECT 
    total_2022,
    total_2024,
    ROUND((( (total_2024::FLOAT / total_2022) ^ 0.5 ) - 1) * 100, 2) AS total_cagr_pct,
    CASE 
        WHEN ROUND((( (total_2024::FLOAT / total_2022) ^ 0.5 ) - 1) * 100, 2) = 13.56 THEN 'PASS'
        ELSE 'FAIL'
    END AS assertion_status
FROM state_cagr;
