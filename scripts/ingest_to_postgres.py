"""
Data Ingestion & Staging Script: AtliQ Motors EV Insights
Translates raw CSV files into structured PostgreSQL seed SQL script with ISO dates.
"""

import os
import sys
import pandas as pd

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(WORKSPACE_DIR, "datasets")
SQL_DIR = os.path.join(WORKSPACE_DIR, "sql")

def generate_seed_sql(dim_date_df, dim_rev_df, makers_df, state_df, output_path):
    """Generates standard PostgreSQL insert statements with ISO dates."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- Seed Data Script: atliq_motors_ev_insights (ISO Dates)\n\n")

        # 1. Dim Date
        f.write("-- 1. Dim Date (36 records)\n")
        f.write("INSERT INTO dim_date (date, fiscal_year, quarter) VALUES\n")
        date_vals = [f"('{row.date}', {row.fiscal_year}, '{row.quarter}')" for _, row in dim_date_df.iterrows()]
        f.write(",\n".join(date_vals) + ";\n\n")

        # 2. Dim Revenue
        f.write("-- 2. Dim Revenue (2 records)\n")
        f.write("INSERT INTO dim_revenue (vehicle_category, average_price) VALUES\n")
        rev_vals = [f"('{row.vehicle_category}', {row.average_price})" for _, row in dim_rev_df.iterrows()]
        f.write(",\n".join(rev_vals) + ";\n\n")

        # 3. Makers Fact (batches of 200)
        f.write("-- 3. Makers Fact (816 records)\n")
        makers_vals = [
            f"('{r.date}', '{r.vehicle_category}', '{str(r.maker).replace(\"'\", \"''\")}', {r.electric_vehicles_sold})"
            for _, r in makers_df.iterrows()
        ]
        for i in range(0, len(makers_vals), 200):
            f.write("INSERT INTO electric_vehicle_sales_by_makers (date, vehicle_category, maker, electric_vehicles_sold) VALUES\n")
            f.write(",\n".join(makers_vals[i:i+200]) + ";\n")
        f.write("\n")

        # 4. State Fact (batches of 200)
        f.write("-- 4. State Fact (2,445 records)\n")
        state_vals = [
            f"('{r.date}', '{str(r.state).replace(\"'\", \"''\")}', '{r.vehicle_category}', {r.electric_vehicles_sold}, {r.total_vehicles_sold})"
            for _, r in state_df.iterrows()
        ]
        for i in range(0, len(state_vals), 200):
            f.write("INSERT INTO electric_vehicle_sales_by_state (date, state, vehicle_category, electric_vehicles_sold, total_vehicles_sold) VALUES\n")
            f.write(",\n".join(state_vals[i:i+200]) + ";\n")

    print(f"Generated seed SQL script: {output_path}")

def main():
    date_path = os.path.join(DATASETS_DIR, "dim_date.csv")
    makers_path = os.path.join(DATASETS_DIR, "electric_vehicle_sales_by_makers.csv")
    state_path = os.path.join(DATASETS_DIR, "electric_vehicle_sales_by_state.csv")

    if not all(os.path.exists(p) for p in [date_path, makers_path, state_path]):
        print("Error: Missing dataset files in datasets/ directory.", file=sys.stderr)
        sys.exit(1)

    dim_date = pd.read_csv(date_path)
    makers = pd.read_csv(makers_path)
    state = pd.read_csv(state_path)

    # Vectorized ISO date standardization
    for df in (dim_date, makers, state):
        df["date"] = pd.to_datetime(df["date"], format="%d-%b-%y").dt.strftime("%Y-%m-%d")

    dim_revenue = pd.DataFrame([
        {"vehicle_category": "2-Wheelers", "average_price": 100000.00},
        {"vehicle_category": "4-Wheelers", "average_price": 1500000.00}
    ])

    os.makedirs(SQL_DIR, exist_ok=True)
    generate_seed_sql(dim_date, dim_revenue, makers, state, os.path.join(SQL_DIR, "seed_data.sql"))

if __name__ == "__main__":
    main()

