"""
Analytical Engine & Discrepancy Resolution: P1-P10 & D2
Calculates ground-truth answers for all primary research questions.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(WORKSPACE_DIR, "datasets")

def parse_date(date_str):
    return datetime.strptime(date_str.strip(), "%d-%b-%y").strftime("%Y-%m-%d")

def run_analytics():
    conn = sqlite3.connect(":memory:")
    
    # Load and prep
    dim_date = pd.read_csv(os.path.join(DATASETS_DIR, "dim_date.csv"))
    makers = pd.read_csv(os.path.join(DATASETS_DIR, "electric_vehicle_sales_by_makers.csv"))
    state = pd.read_csv(os.path.join(DATASETS_DIR, "electric_vehicle_sales_by_state.csv"))

    dim_date["date"] = dim_date["date"].apply(parse_date)
    makers["date"] = makers["date"].apply(parse_date)
    state["date"] = state["date"].apply(parse_date)

    dim_date.to_sql("dim_date", conn, index=False)
    makers.to_sql("electric_vehicle_sales_by_makers", conn, index=False)
    state.to_sql("electric_vehicle_sales_by_state", conn, index=False)

    print("================================================================================")
    print("D2 INVESTIGATION: TOP 3 MAKERS DISCREPANCY ANALYSIS")
    print("================================================================================")
    
    # Check 1: All years 2W sales by maker
    q_all_2w = """
        SELECT maker, SUM(electric_vehicles_sold) as total_sold
        FROM electric_vehicle_sales_by_makers
        WHERE vehicle_category = '2-Wheelers'
        GROUP BY maker
        ORDER BY total_sold DESC
    """
    df_all_2w = pd.read_sql_query(q_all_2w, conn)
    print("\nAll-Years 2-Wheeler Top 5 Makers:")
    print(df_all_2w.head(5).to_string(index=False))

    # Check 2: FY2023 vs FY2024 2W sales by maker
    q_fy_2w = """
        SELECT 
            m.maker,
            SUM(CASE WHEN d.fiscal_year = 2022 THEN m.electric_vehicles_sold ELSE 0 END) as fy2022,
            SUM(CASE WHEN d.fiscal_year = 2023 THEN m.electric_vehicles_sold ELSE 0 END) as fy2023,
            SUM(CASE WHEN d.fiscal_year = 2024 THEN m.electric_vehicles_sold ELSE 0 END) as fy2024,
            SUM(m.electric_vehicles_sold) as total_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '2-Wheelers'
        GROUP BY m.maker
        ORDER BY fy2024 DESC
    """
    df_fy_2w = pd.read_sql_query(q_fy_2w, conn)
    print("\nFY2022, FY2023, FY2024 2-Wheeler Breakdown (Sorted by FY2024):")
    print(df_fy_2w.head(6).to_string(index=False))

    # What filter yields OLA: 475K, TVS: 263K, ATHER: 184K?
    # Let's inspect FY2024 specifically:
    # OLA FY24: 326,455? Or FY23+FY24? Or calendar year?
    q_cy = """
        SELECT 
            m.maker,
            SUBSTR(m.date, 1, 4) as cal_year,
            SUM(m.electric_vehicles_sold) as cal_sold
        FROM electric_vehicle_sales_by_makers m
        WHERE m.vehicle_category = '2-Wheelers'
        GROUP BY m.maker, cal_year
        ORDER BY m.maker, cal_year
    """
    df_cy = pd.read_sql_query(q_cy, conn)
    print("\nCalendar Year Breakdown for OLA, TVS, ATHER:")
    print(df_cy[df_cy['maker'].isin(['OLA ELECTRIC', 'TVS MOTOR COMPANY LTD', 'ATHER ENERGY PVT LTD'])].to_string(index=False))

    # Check if FY23 + FY24 (2 years) or specific quarters:
    q_fy23_24 = """
        SELECT 
            m.maker,
            SUM(m.electric_vehicles_sold) as fy23_24_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '2-Wheelers' AND d.fiscal_year IN (2023, 2024)
        GROUP BY m.maker
        ORDER BY fy23_24_sold DESC
    """
    df_fy23_24 = pd.read_sql_query(q_fy23_24, conn)
    print("\nFY2023 + FY2024 (Last 2 Years) 2-Wheeler Sold:")
    print(df_fy23_24.head(5).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P1: Top 3 & Bottom 3 Makers (FY2023 & FY2024)")
    print("================================================================================")
    
    # FY2023 Top 3 & Bottom 3
    q_p1_2023_top = """
        SELECT maker, SUM(m.electric_vehicles_sold) as fy2023_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '2-Wheelers' AND d.fiscal_year = 2023
        GROUP BY maker
        ORDER BY fy2023_sold DESC
        LIMIT 3
    """
    q_p1_2023_bottom = """
        SELECT maker, SUM(m.electric_vehicles_sold) as fy2023_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '2-Wheelers' AND d.fiscal_year = 2023
        GROUP BY maker
        HAVING fy2023_sold > 0
        ORDER BY fy2023_sold ASC
        LIMIT 3
    """
    print("FY2023 Top 3 (2W):")
    print(pd.read_sql_query(q_p1_2023_top, conn).to_string(index=False))
    print("\nFY2023 Bottom 3 (2W, > 0):")
    print(pd.read_sql_query(q_p1_2023_bottom, conn).to_string(index=False))

    # FY2024 Top 3 & Bottom 3
    q_p1_2024_top = """
        SELECT maker, SUM(m.electric_vehicles_sold) as fy2024_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '2-Wheelers' AND d.fiscal_year = 2024
        GROUP BY maker
        ORDER BY fy2024_sold DESC
        LIMIT 3
    """
    q_p1_2024_bottom = """
        SELECT maker, SUM(m.electric_vehicles_sold) as fy2024_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '2-Wheelers' AND d.fiscal_year = 2024
        GROUP BY maker
        HAVING fy2024_sold > 0
        ORDER BY fy2024_sold ASC
        LIMIT 3
    """
    print("\nFY2024 Top 3 (2W):")
    print(pd.read_sql_query(q_p1_2024_top, conn).to_string(index=False))
    print("\nFY2024 Bottom 3 (2W, > 0):")
    print(pd.read_sql_query(q_p1_2024_bottom, conn).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P2: Top 5 States by Penetration Rate FY2024 (2W, 4W, Combined)")
    print("================================================================================")
    
    # 2W Penetration FY2024
    q_p2_2w = """
        SELECT 
            s.state,
            SUM(s.electric_vehicles_sold) as ev_sold,
            SUM(s.total_vehicles_sold) as total_sold,
            ROUND(SUM(s.electric_vehicles_sold) * 100.0 / SUM(s.total_vehicles_sold), 2) as penetration_pct
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE d.fiscal_year = 2024 AND s.vehicle_category = '2-Wheelers'
        GROUP BY s.state
        ORDER BY penetration_pct DESC
        LIMIT 5
    """
    print("\nTop 5 States - 2-Wheelers Penetration (FY2024):")
    print(pd.read_sql_query(q_p2_2w, conn).to_string(index=False))

    # 4W Penetration FY2024
    q_p2_4w = """
        SELECT 
            s.state,
            SUM(s.electric_vehicles_sold) as ev_sold,
            SUM(s.total_vehicles_sold) as total_sold,
            ROUND(SUM(s.electric_vehicles_sold) * 100.0 / SUM(s.total_vehicles_sold), 2) as penetration_pct
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE d.fiscal_year = 2024 AND s.vehicle_category = '4-Wheelers'
        GROUP BY s.state
        ORDER BY penetration_pct DESC
        LIMIT 5
    """
    print("\nTop 5 States - 4-Wheelers Penetration (FY2024):")
    print(pd.read_sql_query(q_p2_4w, conn).to_string(index=False))

    # Combined Penetration FY2024
    q_p2_comb = """
        SELECT 
            s.state,
            SUM(s.electric_vehicles_sold) as ev_sold,
            SUM(s.total_vehicles_sold) as total_sold,
            ROUND(SUM(s.electric_vehicles_sold) * 100.0 / SUM(s.total_vehicles_sold), 2) as penetration_pct
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE d.fiscal_year = 2024
        GROUP BY s.state
        ORDER BY penetration_pct DESC
        LIMIT 5
    """
    print("\nTop 5 States - Combined 2W+4W Penetration (FY2024):")
    print(pd.read_sql_query(q_p2_comb, conn).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P3: States with Negative Penetration Rate Change (FY22 -> FY24)")
    print("================================================================================")
    q_p3 = """
        WITH pen AS (
            SELECT 
                s.state,
                SUM(CASE WHEN d.fiscal_year = 2022 THEN s.electric_vehicles_sold ELSE 0 END) * 100.0 / 
                    NULLIF(SUM(CASE WHEN d.fiscal_year = 2022 THEN s.total_vehicles_sold ELSE 0 END), 0) as pen_2022,
                SUM(CASE WHEN d.fiscal_year = 2024 THEN s.electric_vehicles_sold ELSE 0 END) * 100.0 / 
                    NULLIF(SUM(CASE WHEN d.fiscal_year = 2024 THEN s.total_vehicles_sold ELSE 0 END), 0) as pen_2024
            FROM electric_vehicle_sales_by_state s
            JOIN dim_date d ON s.date = d.date
            GROUP BY s.state
        )
        SELECT 
            state,
            ROUND(pen_2022, 2) as penetration_fy22,
            ROUND(pen_2024, 2) as penetration_fy24,
            ROUND(pen_2024 - pen_2022, 2) as pen_rate_change
        FROM pen
        WHERE (pen_2024 - pen_2022) < 0
        ORDER BY pen_rate_change ASC
    """
    df_p3 = pd.read_sql_query(q_p3, conn)
    print(f"\nStates with declining penetration rate ({len(df_p3)} states found):")
    print(df_p3.to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P4: Quarterly Sales Trends for Top 5 4W EV Makers")
    print("================================================================================")
    q_top5_4w = """
        SELECT maker, SUM(electric_vehicles_sold) as total_sold
        FROM electric_vehicle_sales_by_makers
        WHERE vehicle_category = '4-Wheelers'
        GROUP BY maker
        ORDER BY total_sold DESC
        LIMIT 5
    """
    df_top5_4w = pd.read_sql_query(q_top5_4w, conn)
    top5_makers = df_top5_4w['maker'].tolist()
    print("Top 5 4-Wheeler EV Makers Overall:", top5_makers)

    q_p4 = f"""
        SELECT 
            m.maker,
            d.fiscal_year,
            d.quarter,
            (d.fiscal_year || ' ' || d.quarter) as fy_quarter,
            SUM(m.electric_vehicles_sold) as units_sold
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '4-Wheelers' AND m.maker IN ({','.join([f"'{m}'" for m in top5_makers])})
        GROUP BY m.maker, d.fiscal_year, d.quarter
        ORDER BY d.fiscal_year, d.quarter, units_sold DESC
    """
    df_p4 = pd.read_sql_query(q_p4, conn)
    pivot_p4 = df_p4.pivot(index='fy_quarter', columns='maker', values='units_sold').fillna(0)
    print("\nQuarterly Sales Volume Matrix:")
    print(pivot_p4.to_string())

    print("\n================================================================================")
    print("PRIMARY QUESTION P5: Delhi vs. Karnataka Comparison (FY2024)")
    print("================================================================================")
    q_p5 = """
        SELECT 
            s.state,
            s.vehicle_category,
            SUM(s.electric_vehicles_sold) as ev_sold,
            SUM(s.total_vehicles_sold) as total_sold,
            ROUND(SUM(s.electric_vehicles_sold) * 100.0 / SUM(s.total_vehicles_sold), 2) as penetration_pct
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE d.fiscal_year = 2024 AND s.state IN ('Delhi', 'Karnataka')
        GROUP BY s.state, s.vehicle_category
        UNION ALL
        SELECT 
            s.state,
            'Combined' as vehicle_category,
            SUM(s.electric_vehicles_sold) as ev_sold,
            SUM(s.total_vehicles_sold) as total_sold,
            ROUND(SUM(s.electric_vehicles_sold) * 100.0 / SUM(s.total_vehicles_sold), 2) as penetration_pct
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE d.fiscal_year = 2024 AND s.state IN ('Delhi', 'Karnataka')
        GROUP BY s.state
        ORDER BY state, vehicle_category
    """
    print(pd.read_sql_query(q_p5, conn).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P6: CAGR for Top 5 4W EV Makers (FY2022 -> FY2024)")
    print("================================================================================")
    q_p6 = f"""
        SELECT 
            m.maker,
            SUM(CASE WHEN d.fiscal_year = 2022 THEN m.electric_vehicles_sold ELSE 0 END) as sales_fy22,
            SUM(CASE WHEN d.fiscal_year = 2024 THEN m.electric_vehicles_sold ELSE 0 END) as sales_fy24
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        WHERE m.vehicle_category = '4-Wheelers' AND m.maker IN ({','.join([f"'{m}'" for m in top5_makers])})
        GROUP BY m.maker
    """
    df_p6 = pd.read_sql_query(q_p6, conn)
    df_p6['cagr_pct'] = df_p6.apply(
        lambda r: round(((r['sales_fy24'] / r['sales_fy22']) ** 0.5 - 1) * 100, 2) if r['sales_fy22'] > 0 else None,
        axis=1
    )
    print(df_p6.sort_values(by='cagr_pct', ascending=False).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P7: Top 10 States by CAGR in Total Vehicles Sold (FY22 -> FY24)")
    print("================================================================================")
    q_p7 = """
        SELECT 
            s.state,
            SUM(CASE WHEN d.fiscal_year = 2022 THEN s.total_vehicles_sold ELSE 0 END) as total_fy22,
            SUM(CASE WHEN d.fiscal_year = 2024 THEN s.total_vehicles_sold ELSE 0 END) as total_fy24
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        GROUP BY s.state
        HAVING total_fy22 > 0
    """
    df_p7 = pd.read_sql_query(q_p7, conn)
    df_p7['cagr_pct'] = round(((df_p7['total_fy24'] / df_p7['total_fy22']) ** 0.5 - 1) * 100, 2)
    print(df_p7.sort_values(by='cagr_pct', ascending=False).head(10).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P8: Peak and Low Season Months for EV Sales (FY2022-FY2024)")
    print("================================================================================")
    q_p8 = """
        SELECT 
            SUBSTR(m.date, 6, 2) as month_num,
            CASE SUBSTR(m.date, 6, 2)
                WHEN '01' THEN 'January'
                WHEN '02' THEN 'February'
                WHEN '03' THEN 'March'
                WHEN '04' THEN 'April'
                WHEN '05' THEN 'May'
                WHEN '06' THEN 'June'
                WHEN '07' THEN 'July'
                WHEN '08' THEN 'August'
                WHEN '09' THEN 'September'
                WHEN '10' THEN 'October'
                WHEN '11' THEN 'November'
                WHEN '12' THEN 'December'
            END as month_name,
            SUM(m.electric_vehicles_sold) as total_ev_sold,
            ROUND(AVG(m.electric_vehicles_sold), 0) as avg_monthly_sold
        FROM electric_vehicle_sales_by_makers m
        GROUP BY month_num, month_name
        ORDER BY total_ev_sold DESC
    """
    df_p8 = pd.read_sql_query(q_p8, conn)
    print(df_p8.to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P9: Projected 2030 EV Sales for Top 10 Penetration States")
    print("================================================================================")
    # Top 10 states by FY2024 penetration rate
    q_top10_states = """
        SELECT 
            s.state,
            SUM(s.electric_vehicles_sold) as ev_fy24,
            SUM(s.total_vehicles_sold) as total_fy24,
            SUM(s.electric_vehicles_sold) * 100.0 / SUM(s.total_vehicles_sold) as pen_fy24
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE d.fiscal_year = 2024
        GROUP BY s.state
        ORDER BY pen_fy24 DESC
        LIMIT 10
    """
    df_top10_states = pd.read_sql_query(q_top10_states, conn)
    top10_list = df_top10_states['state'].tolist()

    q_p9 = f"""
        SELECT 
            s.state,
            SUM(CASE WHEN d.fiscal_year = 2022 THEN s.electric_vehicles_sold ELSE 0 END) as ev_fy22,
            SUM(CASE WHEN d.fiscal_year = 2024 THEN s.electric_vehicles_sold ELSE 0 END) as ev_fy24
        FROM electric_vehicle_sales_by_state s
        JOIN dim_date d ON s.date = d.date
        WHERE s.state IN ({','.join([f"'{s}'" for s in top10_list])})
        GROUP BY s.state
    """
    df_p9 = pd.read_sql_query(q_p9, conn)
    df_p9 = df_p9.merge(df_top10_states[['state', 'pen_fy24']], on='state')
    df_p9['ev_cagr'] = (df_p9['ev_fy24'] / df_p9['ev_fy22']) ** 0.5 - 1
    # Compounding 6 years: 2024 to 2030
    df_p9['projected_ev_2030'] = round(df_p9['ev_fy24'] * ((1 + df_p9['ev_cagr']) ** 6))
    df_p9['ev_cagr_pct'] = round(df_p9['ev_cagr'] * 100, 2)
    df_p9['pen_fy24_pct'] = round(df_p9['pen_fy24'], 2)
    print(df_p9[['state', 'pen_fy24_pct', 'ev_fy22', 'ev_fy24', 'ev_cagr_pct', 'projected_ev_2030']].sort_values(by='pen_fy24_pct', ascending=False).to_string(index=False))

    print("\n================================================================================")
    print("PRIMARY QUESTION P10: Revenue Growth Rate Model (FY22 vs FY24 & FY23 vs FY24)")
    print("================================================================================")
    # Using industry empirical average prices:
    # 2-Wheelers: ₹1,00,000 (INR 1 Lakh)
    # 4-Wheelers: ₹15,00,000 (INR 15 Lakhs)
    asp_2w = 100000.0
    asp_4w = 1500000.0

    q_rev = """
        SELECT 
            m.vehicle_category,
            SUM(CASE WHEN d.fiscal_year = 2022 THEN m.electric_vehicles_sold ELSE 0 END) as units_fy22,
            SUM(CASE WHEN d.fiscal_year = 2023 THEN m.electric_vehicles_sold ELSE 0 END) as units_fy23,
            SUM(CASE WHEN d.fiscal_year = 2024 THEN m.electric_vehicles_sold ELSE 0 END) as units_fy24
        FROM electric_vehicle_sales_by_makers m
        JOIN dim_date d ON m.date = d.date
        GROUP BY m.vehicle_category
    """
    df_rev = pd.read_sql_query(q_rev, conn)
    df_rev['asp'] = df_rev['vehicle_category'].map({'2-Wheelers': asp_2w, '4-Wheelers': asp_4w})
    df_rev['rev_fy22_cr'] = round((df_rev['units_fy22'] * df_rev['asp']) / 1e7, 2)
    df_rev['rev_fy23_cr'] = round((df_rev['units_fy23'] * df_rev['asp']) / 1e7, 2)
    df_rev['rev_fy24_cr'] = round((df_rev['units_fy24'] * df_rev['asp']) / 1e7, 2)

    df_rev['growth_22_24_pct'] = round(((df_rev['rev_fy24_cr'] - df_rev['rev_fy22_cr']) / df_rev['rev_fy22_cr']) * 100, 2)
    df_rev['growth_23_24_pct'] = round(((df_rev['rev_fy24_cr'] - df_rev['rev_fy23_cr']) / df_rev['rev_fy23_cr']) * 100, 2)

    print("\nRevenue Table by Vehicle Category (in INR Crores):")
    print(df_rev[['vehicle_category', 'asp', 'rev_fy22_cr', 'rev_fy23_cr', 'rev_fy24_cr', 'growth_22_24_pct', 'growth_23_24_pct']].to_string(index=False))

    total_fy22_rev = df_rev['rev_fy22_cr'].sum()
    total_fy23_rev = df_rev['rev_fy23_cr'].sum()
    total_fy24_rev = df_rev['rev_fy24_cr'].sum()
    overall_growth_22_24 = round(((total_fy24_rev - total_fy22_rev) / total_fy22_rev) * 100, 2)
    overall_growth_23_24 = round(((total_fy24_rev - total_fy23_rev) / total_fy23_rev) * 100, 2)
    print(f"\nOverall Revenue: FY22=INR {total_fy22_rev:.2f} Cr, FY23=INR {total_fy23_rev:.2f} Cr, FY24=INR {total_fy24_rev:.2f} Cr")
    print(f"Overall Revenue Growth FY22->FY24: {overall_growth_22_24}%")
    print(f"Overall Revenue Growth FY23->FY24: {overall_growth_23_24}%")

if __name__ == "__main__":
    run_analytics()
