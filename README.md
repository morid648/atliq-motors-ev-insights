# AtliQ Motors — India Electric Vehicle Market-Entry Strategy & Analytics

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Anshul_Chaudhary-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/anshul-chaudhary-508138308/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/morid648/atliq-motors-ev-insights/blob/main/sql/schema.sql)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://github.com/morid648/atliq-motors-ev-insights/blob/main/dax/measures.dax)
[![DAX](https://img.shields.io/badge/DAX-Calculation_Engine-0078D4?style=for-the-badge&logoColor=white)](https://github.com/morid648/atliq-motors-ev-insights/blob/main/dax/measures.dax)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/morid648/atliq-motors-ev-insights/blob/main/scripts/ingest_to_postgres.py)
[![Status](https://img.shields.io/badge/Status-Completed_%26_Validated-success?style=for-the-badge)](https://github.com/morid648/atliq-motors-ev-insights/blob/main/docs/RESULTS.md)

---

## 📌 Executive Summary & Business Problem

**AtliQ Motors**, an automotive OEM commanding a **25% EV/hybrid market share in North America**, is strategizing expansion into India where its current market presence is under **2%**. 

To determine the optimal commercial entry roadmap, **Bruce Haryali (Chief, AtliQ Motors India)** commissioned lead data analyst **Peter Pandey** to conduct an end-to-end market feasibility study. Rather than a superficial descriptive dashboard, leadership mandated answering **16 specific, high-impact business questions** (10 data-driven primary questions and 6 external research-backed strategic questions) spanning consumer adoption trends, maker competitiveness, state-level penetration, seasonality, fiscal forecasting, and manufacturing logistics.

This project synthesizes **57,220,252 automotive vehicle registrations** and **2,066,111 EV sales** across 35 Indian states and union territories over 3 fiscal years (**FY2022 to FY2024**).

---

## 🏗 End-to-End Data Pipeline & Architecture

Unlike typical portfolio projects that directly ingest flat CSVs into BI tools, this project adheres to enterprise data engineering standards by establishing a **PostgreSQL relational staging layer** with strict schema enforcement, ISO date standardization, and primary/foreign key integrity before feeding a **Power BI Semantic Star Schema**.

```
┌─────────────────────────┐       ┌──────────────────────────────┐       ┌────────────────────────────┐
│   3 Raw Source CSVs     │       │  PostgreSQL Relational Layer │       │   Power BI Semantic Model  │
│ • dim_date.csv (36 rows)│  ───► │ • Schema DDL & PK/FK Indexes │  ───► │ • Star Schema (No M:M)     │
│ • makers_sales (816 r)  │  ETL  │ • ISO Date Normalization     │ Direct│ • 24+ Corrected DAX Measures│
│ • state_sales (2,445 r) │       │ • Data Quality Assertions    │ Query │ • Interactive 3-Page UI    │
└─────────────────────────┘       └──────────────────────────────┘       └────────────────────────────┘
```

### 1. Relational Staging ([`sql/schema.sql`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/sql/schema.sql))
- Normalized date strings (`DD-MMM-YY`) into ISO `YYYY-MM-DD` timestamps.
- Defined relational tables (`dim_date`, `dim_revenue`, `electric_vehicle_sales_by_makers`, `electric_vehicle_sales_by_state`) with enforced data types, foreign keys, and B-tree indexes on join attributes.
- Built reproducible ingestion pipelines in Python ([`scripts/ingest_to_postgres.py`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/scripts/ingest_to_postgres.py)) and seed SQL dump ([`sql/seed_data.sql`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/sql/seed_data.sql)).

### 2. Star Schema Topology ([`docs/ANALYSIS.md`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/docs/ANALYSIS.md))
- **Fact Tables:**
  - `electric_vehicle_sales_by_makers` (Grain: `date` × `vehicle_category` × `maker`)
  - `electric_vehicle_sales_by_state` (Grain: `date` × `state` × `vehicle_category`)
- **Dimension Tables:**
  - `dim_date` (Grain: monthly date, `fiscal_year`, `quarter`)
  - `dim_revenue` (Grain: `vehicle_category`, empirical average selling price)
- **Zero Fact-to-Fact Relationships:** Clean 1-to-many filtering preventing ambiguous paths or split-grain calculation errors.

---

## 🛠 Critical Engineering Catches & Data Governance

A core differentiator of this project is discovering and fixing upstream defects rather than blindly visualizing flawed data.

### 1. Defect D1 Rectification (Reference DAX Measure Bug)
In the provided reference DAX specification file (`DAX_Measures_And_Calculated_Columns_AtliQ_Motors.xlsx`), the `2024 Revenue` measure contained a copy-paste error:
```dax
-- AS SUPPLIED IN REFERENCE (Defective):
2024 Revenue = CALCULATE(SUMX(...), dim_date[fiscal_year] = 2023)  -- BUG: Filtered on 2023!
```
**Impact:** Because `2024 Revenue` evaluated identical data to `2023 Revenue`, the downstream measure `Revenue Growth Rate 2023-2024` computed to **exactly 0%**, completely falsifying the answer to business question **P10**.

**The Fix ([`dax/measures.dax`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/dax/measures.dax)):**
Corrected the filter to `dim_date[fiscal_year] = 2024`. True revenue growth rate is **+55.31%** (from ₹14,398.78 Cr in FY23 to ₹22,362.07 Cr in FY24), preserving financial reporting integrity.

### 2. Discrepancy D2 Resolution (Filter-State Forensic Audit)
- **Discrepancy:** The dashboard reference walkthrough displayed Top 3 Makers as *OLA (475K), TVS (263K), Ather (184K)*, which differed from both single-year FY24 numbers and all-time totals.
- **Root-Cause Discovery:** Recomputation proved that the visual was captured with a multi-select slicer state covering **FY2023 + FY2024 combined** (OLA: 152,583 + 322,489 = **475,072**; TVS: 82,093 + 180,743 = **262,836**; Ather: 76,921 + 107,552 = **184,473**).
- **Resolution:** Provided complete audit transparency by reporting exact single-year benchmarks for question **P1** while explaining the multi-year UI filter state.

### 3. Automated Test Assertion Suite ([`scripts/test_pipeline_assertions.py`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/scripts/test_pipeline_assertions.py))
Automated Python test harness executing 7 validation suites across PostgreSQL and flat files:
- 100% row count match (`dim_date`: 36, `makers`: 816, `state`: 2,445).
- Zero orphaned foreign keys.
- Cross-table metric parity (`SUM(electric_vehicles_sold)` across makers equals state sales = **2,066,111 units**).

---

## 📊 Key Findings & Results Matrix

| # | Question / Topic | Key Empirical Finding | Strategic Value & Context |
|:---:|:---|:---|:---|
| **P1** | **Top & Bottom 2W Makers** | **FY23 Top:** OLA (152.6K), Okinawa (96.9K), Hero (89.0K)<br>**FY24 Top:** OLA (322.5K), TVS (180.7K), Ather (107.6K) | OLA & TVS doubled volume; legacy 2W OEMs lost share after FAME-II subsidy audits. |
| **P2** | **Top Adoption States (FY24)** | **Goa (13.75%)**, **Kerala (11.59%)**, **Karnataka (10.18%)**, **Maharashtra (8.60%)** | Coastal Southern/Western states form India's prime EV adoption corridor. |
| **P3** | **Declining Penetration States** | **FY22→FY24:** 0 states declined.<br>**FY23→FY24:** 6 states dipped (RJ, HR, UK, GJ, JH, HP). | June 2023 FAME-II subsidy reduction caused temporary adoption friction in price-sensitive northern states. |
| **P4** | **4W EV Quarterly Trends** | **Tata Motors:** 88,935 units (commands **>68% market share**)<br>**Mahindra:** 41,193 units | Incumbents dominate by electrifying established ICE compact crossover architectures. |
| **P5** | **Delhi vs. Karnataka (FY24)** | **Karnataka:** 161,248 EVs (10.18% pen)<br>**Delhi:** 47,381 EVs (7.71% pen) | Karnataka wins on scale (3.4x volume); Delhi leads slightly in 4W penetration (4.29% vs 4.26%). |
| **P6** | **Top 4W Makers CAGR** | **BYD:** 566.5% \| **Hyundai:** 255.5% \| **M&M:** 140.3% \| **MG:** 131.5% \| **Tata:** 94.7% | High momentum among challenger 4W OEMs expanding the electric crossover segment. |
| **P7** | **Auto Retail Market CAGR** | **Meghalaya (28.5%)**, **Goa (27.4%)**, **Karnataka (25.3%)** | High EV adoption states also lead the nation in overall automotive retail sales growth. |
| **P8** | **EV Sales Seasonality** | **Peak:** March (291.6K) & November (205.3K)<br>**Trough:** June (106.7K) & July (127.2K) | Peaks coincide with FY-end corporate tax depreciation incentives (Q4) and festive Diwali purchases. |
| **P9** | **2030 Compounding Forecast** | Top states compound to **13.3M units (MH)**, **11.8M (KL)**, **8.4M (KA)** | Constant-CAGR projection highlights massive long-term scale in the Southern belt. |
| **P10**| **Revenue Growth by Category** | **Overall EV Revenue:** ₹5,312 Cr (FY22) ➔ ₹22,362 Cr (FY24) (**+320.95%**)<br>4W Segment: **+367.79%** | 4-Wheelers generate **58.3% of total industry revenue** despite representing only 7.4% of unit volume. |

> *For full mathematical tables, detailed charts, and external research citations on questions S1–S6, see [`docs/RESULTS.md`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/docs/RESULTS.md).*

---

## 🎯 Strategic Recommendations for AtliQ Motors Leadership

Based on the synthesis of empirical data and secondary automotive research ([`docs/PROJECT_REPORT.md`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/docs/PROJECT_REPORT.md)):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ATLIQ MOTORS INDIA MARKET-ENTRY PLAYBOOK                        │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│   1. PRODUCT STRATEGY      │   2. GEOGRAPHIC PHASING     │   3. MANUFACTURING & BRAND  │
│ • Midsize Electric SUV     │ • "South Corridor First"    │ • Tamil Nadu Plant          │
│ • Price: ₹18L – ₹25L       │ • Hubs: BLR, COK, GOA, BOM  │ • 3 Major Deepwater Ports   │
│ • 400+ km range, ADAS L2   │ • High fast-charger density │ • Ambassador: Neeraj Chopra │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────┘
```

1. **Product Positioning & Segment Choice:**
   - **Avoid:** Ultra-luxury CBU sedans (>₹60 Lakhs), where total addressable national annual volume is <3,000 units.
   - **Target:** A localized **midsize electric crossover / SUV priced at ₹18–25 Lakhs** (60 kWh battery, 400+ km real-world range). Compete directly against Tata Curvv EV and MG ZS EV with superior US-engineered battery thermal management and active cabin cooling.
2. **Geographic Phasing ("South-First" Corridor):**
   - Focus Phase 1 rollout on **Bengaluru (KA), Kochi (KL), Panaji (GA), Chennai (TN), and Mumbai-Pune (MH)**.
   - These 5 markets represent over 52% of national EV demand, provide 100% state road-tax waivers, and host >55% of India's public DC fast-charging network.
3. **Manufacturing Base in Tamil Nadu (Hosur/Sriperumbudur):**
   - Tap into India's densest EV component supply chain (Ola, TVS, Ather, Hyundai).
   - Leverage 3 deepwater ports (Chennai, Ennore, Tuticorin) for battery component imports and finished-vehicle export.
4. **Brand Ambassadorship:**
   - Partner with **Neeraj Chopra** (Olympic Champion) to project precision engineering, athletic stamina, and youth aspiration, building immediate domestic trust.

---

## 💻 Tech Stack & Key DAX Measures

- **Database:** PostgreSQL 15 (DDL Schema, Primary/Foreign Keys, B-tree Indexes, SQL Assertions)
- **ETL & Data Science:** Python 3.10+, Pandas, SQLAlchemy, NumPy
- **Business Intelligence:** Power BI Desktop, DAX Time-Intelligence & Financial Modeling
- **Version Control & Quality:** Git, Markdown, Markdown Linting

### Highlight DAX Formulas ([`dax/measures.dax`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/dax/measures.dax))

```dax
-- 1. Compound Annual Growth Rate (CAGR) for EV Sales
CAGR for EV Sales = 
VAR EndValue = CALCULATE([Total EV sales per makers], dim_date[fiscal_year] = 2024)
VAR StartValue = CALCULATE([Total EV sales per makers], dim_date[fiscal_year] = 2022)
VAR Periods = 2
RETURN
IF(StartValue > 0, ((EndValue / StartValue) ^ (1 / Periods)) - 1, BLANK())

-- 2. 2030 Compounding EV Sales Forecast (Answers P9)
Projected EV Sales 2030 = 
VAR CurrentEVSales = CALCULATE([Total EV Sales per State], dim_date[fiscal_year] = 2024)
VAR CAGREVSales = [CAGR EV Sales For States]
VAR YearsToProject = 6
RETURN
IF(NOT ISBLANK(CAGREVSales), CurrentEVSales * (1 + CAGREVSales) ^ YearsToProject, BLANK())

-- 3. Corrected Revenue Engine (Defect D1 Rectified)
2024 Revenue = 
CALCULATE(
    SUMX(
        'electric_vehicle_sales_by_makers',
        'electric_vehicle_sales_by_makers'[electric_vehicles_sold]
            * LOOKUPVALUE('Revenue'[Average Price], 'Revenue'[Vehicle_category], 'electric_vehicle_sales_by_makers'[vehicle_category])
    ),
    dim_date[fiscal_year] = 2024
)
```

---

## 📁 Repository Structure & Documentation Suite

```
├── README.md                            <- Executive overview, pipeline, findings, recommendations (You are here)
├── sql/
│   ├── schema.sql                       <- PostgreSQL DDL scripts with PK/FK constraints & indexes
│   ├── seed_data.sql                    <- Sanitized SQL data insertion script
│   └── integrity_checks.sql             <- SQL assertion & test suite
├── dax/
│   └── measures.dax                     <- Production DAX calculation library (24+ verified measures)
├── scripts/
│   ├── ingest_to_postgres.py            <- Automated ETL pipeline (CSV ➔ PostgreSQL)
│   ├── compute_analytical_queries.py    <- Python ground-truth analytics engine (P1–P10)
│   └── test_pipeline_assertions.py      <- Automated data-quality & relational integrity test suite
├── docs/
│   ├── RESULTS.md                       <- Comprehensive, verified answers to all 16 research questions
│   ├── ROOT_CAUSE_ANALYSIS.md           <- In-depth technical & macroeconomic Root Cause Analyses (RCA)
│   ├── ANALYSIS.md                      <- Technical deep dive into data modeling, grain, and queries
│   ├── PROJECT_REPORT.md                <- Executive briefing & strategic market-entry playbook for leadership
│   └── END_USER_GUIDE.md                <- Dashboard navigation manual, filter guide, and UI specifications
├── datasets/                            <- Raw source CSVs (dim_date, makers_sales, state_sales)
├── meta_data.txt                        <- Column definitions & dataset schema notes
└── .gitignore                           <- Git hygiene and data security rules
```

---

## ⚡ How to Reproduce & Run

### 1. Clone & Set Up Database
```bash
git clone https://github.com/morid648/atliq-motors-ev-insights.git
cd atliq-motors-ev-insights
```

### 2. Ingest Data to PostgreSQL
Configure your PostgreSQL credentials in `scripts/ingest_to_postgres.py` or `.env` and run:
```bash
python scripts/ingest_to_postgres.py
```

### 3. Run Validation Tests & Analytics Suite
```bash
python scripts/test_pipeline_assertions.py
python scripts/compute_analytical_queries.py
```

### 4. Connect Power BI
1. Open Power BI Desktop ➔ **Get Data ➔ PostgreSQL Database**.
2. Connect to your local database to import `dim_date`, `electric_vehicle_sales_by_makers`, and `electric_vehicle_sales_by_state`.
3. Create the `Revenue` dimension table (`2-Wheelers`: ₹1,00,000, `4-Wheelers`: ₹15,00,000).
4. Copy the measures from [`dax/measures.dax`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/dax/measures.dax) into your model.

---

## 🏆 Recruiter & Reviewer Takeaways

- **Data Engineering Discipline:** Staged raw data through PostgreSQL with formal schemas, constraints, and automated integrity validation before modeling in BI.
- **Analytical Rigor & Critical Thinking:** Identified and corrected a critical formula error in the supplied DAX reference file, preventing a false 0% revenue growth reporting error.
- **Business Acumen & Strategic Translation:** Translated 57M+ data points into actionable market entry recommendations spanning product segment, pricing, geographic phasing, and manufacturing site selection.
- **Enterprise-Ready Documentation:** Structured, cross-linked documentation suite catering to executive stakeholders, technical engineers, and end-users.

---
*Created as part of the Codebasics Data Analytics Project Challenge.*

