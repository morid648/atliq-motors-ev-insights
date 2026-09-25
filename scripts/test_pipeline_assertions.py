"""
Pipeline & SQL Assertion Verification Suite
Loads ISO data into in-memory SQLite and asserts 100% data integrity before analytics.
"""

import os
import sqlite3
import pandas as pd

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(WORKSPACE_DIR, "datasets")

def run_assertions():
    conn = sqlite3.connect(":memory:")

    # Load and standardize data
    dim_date = pd.read_csv(os.path.join(DATASETS_DIR, "dim_date.csv"))
    makers = pd.read_csv(os.path.join(DATASETS_DIR, "electric_vehicle_sales_by_makers.csv"))
    state = pd.read_csv(os.path.join(DATASETS_DIR, "electric_vehicle_sales_by_state.csv"))

    for df in (dim_date, makers, state):
        df["date"] = pd.to_datetime(df["date"], format="%d-%b-%y").dt.strftime("%Y-%m-%d")

    dim_revenue = pd.DataFrame([
        {"vehicle_category": "2-Wheelers", "average_price": 100000.0},
        {"vehicle_category": "4-Wheelers", "average_price": 1500000.0}
    ])

    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    dim_revenue.to_sql("dim_revenue", conn, if_exists="append", index=False)
    makers.to_sql("electric_vehicle_sales_by_makers", conn, if_exists="append", index=False)
    state.to_sql("electric_vehicle_sales_by_state", conn, if_exists="append", index=False)

    cursor = conn.cursor()
    print("=== RUNNING ASSERTIONS ===")
    
    # 1. Row counts
    counts = {
        "dim_date": cursor.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0],
        "dim_revenue": cursor.execute("SELECT COUNT(*) FROM dim_revenue").fetchone()[0],
        "makers": cursor.execute("SELECT COUNT(*) FROM electric_vehicle_sales_by_makers").fetchone()[0],
        "state": cursor.execute("SELECT COUNT(*) FROM electric_vehicle_sales_by_state").fetchone()[0],
    }
    assert counts["dim_date"] == 36, f"dim_date count failed: {counts['dim_date']}"
    assert counts["dim_revenue"] == 2, f"dim_revenue count failed: {counts['dim_revenue']}"
    assert counts["makers"] == 816, f"makers count failed: {counts['makers']}"
    assert counts["state"] == 2445, f"state count failed: {counts['state']}"
    print(f"[PASS] Row counts verified: {counts}")

    # 2. Total sales equality
    ev_makers = cursor.execute("SELECT SUM(electric_vehicles_sold) FROM electric_vehicle_sales_by_makers").fetchone()[0]
    ev_state = cursor.execute("SELECT SUM(electric_vehicles_sold) FROM electric_vehicle_sales_by_state").fetchone()[0]
    total_veh = cursor.execute("SELECT SUM(total_vehicles_sold) FROM electric_vehicle_sales_by_state").fetchone()[0]
    assert ev_makers == 2066111, f"EV makers sum failed: {ev_makers}"
    assert ev_state == 2066111, f"EV state sum failed: {ev_state}"
    assert total_veh == 57220252, f"Total vehicles sum failed: {total_veh}"
    print(f"[PASS] Total volume verified: EV Sales={ev_makers}, Total Vehicles={total_veh}")

    # 3. Penetration rate
    pen_rate = round((ev_state / total_veh) * 100, 2)
    assert pen_rate == 3.61, f"Penetration rate failed: {pen_rate}"
    print(f"[PASS] Penetration rate verified: {pen_rate}%")

    # 4. EV Sales CAGR (FY22 -> FY24)
    ev_22 = cursor.execute("""
        SELECT SUM(m.electric_vehicles_sold) 
        FROM electric_vehicle_sales_by_makers m 
        JOIN dim_date d ON m.date = d.date 
        WHERE d.fiscal_year = 2022
    """).fetchone()[0]
    ev_24 = cursor.execute("""
        SELECT SUM(m.electric_vehicles_sold) 
        FROM electric_vehicle_sales_by_makers m 
        JOIN dim_date d ON m.date = d.date 
        WHERE d.fiscal_year = 2024
    """).fetchone()[0]
    ev_cagr = round(((ev_24 / ev_22) ** 0.5 - 1) * 100, 2)
    assert ev_22 == 271150 and ev_24 == 1019593 and ev_cagr == 93.91
    print(f"[PASS] EV Sales CAGR verified: {ev_cagr}% (FY22: {ev_22} -> FY24: {ev_24})")

    # 5. Total Vehicles CAGR (FY22 -> FY24)
    tot_22 = cursor.execute("""
        SELECT SUM(s.total_vehicles_sold) 
        FROM electric_vehicle_sales_by_state s 
        JOIN dim_date d ON s.date = d.date 
        WHERE d.fiscal_year = 2022
    """).fetchone()[0]
    tot_24 = cursor.execute("""
        SELECT SUM(s.total_vehicles_sold) 
        FROM electric_vehicle_sales_by_state s 
        JOIN dim_date d ON s.date = d.date 
        WHERE d.fiscal_year = 2024
    """).fetchone()[0]
    tot_cagr = round(((tot_24 / tot_22) ** 0.5 - 1) * 100, 2)
    assert tot_22 == 16421824 and tot_24 == 21177249 and tot_cagr == 13.56
    print(f"[PASS] Total Vehicles CAGR verified: {tot_cagr}% (FY22: {tot_22} -> FY24: {tot_24})")

    # 6. Category breakdown
    sold_2w = cursor.execute("SELECT SUM(electric_vehicles_sold) FROM electric_vehicle_sales_by_makers WHERE vehicle_category = '2-Wheelers'").fetchone()[0]
    sold_4w = cursor.execute("SELECT SUM(electric_vehicles_sold) FROM electric_vehicle_sales_by_makers WHERE vehicle_category = '4-Wheelers'").fetchone()[0]
    assert sold_2w == 1913168 and sold_4w == 152943
    print(f"[PASS] Category breakdown verified: 2-Wheelers={sold_2w}, 4-Wheelers={sold_4w}")

    print("\nALL ASSERTIONS PASSED WITH 100% PARITY!")

if __name__ == "__main__":
    run_assertions()
