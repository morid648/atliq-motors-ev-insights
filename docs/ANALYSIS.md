# ANALYSIS.md — Methodology, Data Architecture & Pipeline Analysis
## AtliQ Motors India EV Market-Entry Study

---

## 1. System Architecture & End-to-End Pipeline

This project adheres strictly to the mandated enterprise architecture:
```
Raw CSV Files (datasets/)
      │
      ▼
Python Transformation & Ingestion Layer (scripts/ingest_to_postgres.py)
      │
      ▼
PostgreSQL Relational Staging Layer (sql/schema.sql, sql/seed_data.sql)
      │
      ▼
Power BI Semantic Star Schema Model (dax/measures.dax)
      │
      ▼
3-Page Analytical Report UI (Home / Maker's Analysis / State Analysis)
```

### 1.1 Why Staging Through PostgreSQL is Mandatory
Standard Power BI projects often connect directly to raw CSV files. For AtliQ Motors, analytical operations standardize on PostgreSQL. The staging database enforces relational integrity, validates date types, verifies grain boundaries, and ensures analytical models are not coupled to flat-file quirks.

---

## 2. Relational Schema & Grain Discipline

```
       electric_vehicle_sales_by_makers (Fact)
       Rows: 816
       Grain: date x vehicle_category x maker
              │                     │
     date (*) │                     │ vehicle_category (*)
              ▼                     ▼
        dim_date (Dim)        dim_revenue (Dim)
        Rows: 36              Rows: 2
        Grain: date           Grain: vehicle_category
              ▲                     ▲
     date (*) │                     │ vehicle_category (*)
              │                     │
       electric_vehicle_sales_by_state (Fact)
       Rows: 2,445
       Grain: date x state x vehicle_category
```

### 2.1 Grain Isolation
- `electric_vehicle_sales_by_makers` records volume at the **maker** level.
- `electric_vehicle_sales_by_state` records volume and total vehicle registrations at the **state** level.
- **Critical Rule:** The two fact tables **never join directly** to one another. There is no shared key between maker and state in the source data. Attempting a direct join creates a many-to-many Cartesian explosion. Both facts filter through shared dimensions (`dim_date` and `dim_revenue`).

---

## 3. Discrepancy Diagnosis & Defect Rectification

### 3.1 Defect D1: `2024 Revenue` DAX Formula Bug
- **As Supplied:**
  ```dax
  2024 Revenue =
  CALCULATE(
      SUMX('electric_vehicle_sales_by_makers', ...),
      dim_date[fiscal_year] = 2023  -- BUG: Copy-paste error from 2023 Revenue
  )
  ```
- **Consequence:** `Revenue Growth Rate 2023-2024` evaluates to $\frac{2024\text{ Revenue} - 2023\text{ Revenue}}{2023\text{ Revenue}} = \frac{X - X}{X} = \mathbf{0\%}$.
- **Resolution:** Updated filter to `dim_date[fiscal_year] = 2024`. True revenue growth rate is **+55.31%** (from ₹14,398.78 Cr to ₹22,362.07 Cr).

### 3.2 Discrepancy D2: Walkthrough Top 3 Makers Filter Reconciliation
- **Observed Numbers:** OLA ELECTRIC (475K), TVS (263K), ATHER (184K).
- **All-Time Numbers:** OLA (489K), TVS (272K), ATHER (204K).
- **Root Cause:** Slicer on the walkthrough GIF was multi-selected for **FY2023 and FY2024** (excluding FY2022):
  - OLA: $152,583 + 322,489 = \mathbf{475,072}$ (475K)
  - TVS: $82,093 + 180,743 = \mathbf{262,836}$ (263K)
  - ATHER: $76,921 + 107,552 = \mathbf{184,473}$ (184K)
- **Status:** **Resolved.** Individual fiscal year numbers are reported for P1.

---

## 4. Analytical Formula Specifications

### 4.1 Penetration Rate
$$\text{Penetration Rate} = \frac{\sum \text{electric\_vehicles\_sold}}{\sum \text{total\_vehicles\_sold}} \times 100$$
- Evaluates to **3.61%** across the entire 3-year market window (2,066,111 EV units / 57,220,252 total vehicles).

### 4.2 Compound Annual Growth Rate (CAGR)
$$\text{CAGR} = \left(\frac{\text{Ending Value}}{\text{Beginning Value}}\right)^{\frac{1}{n}} - 1$$
- For FY2022 to FY2024, $n = 2$ fiscal years.
- EV Sales CAGR: $\left(\frac{1,019,593}{271,150}\right)^{0.5} - 1 = \mathbf{93.91\%}$.
- Total Vehicles Sold CAGR: $\left(\frac{21,177,249}{16,421,824}\right)^{0.5} - 1 = \mathbf{13.56\%}$.

### 4.3 2030 Compounding Projection
$$\text{Sales}_{2030} = \text{Sales}_{2024} \times (1 + \text{CAGR})^6$$
- Projects 6 compounding years beyond FY2024.
