# ROOT_CAUSE_ANALYSIS.md — Engineering & Analytical RCA
## AtliQ Motors India EV Insights Project
> **Author:** Peter Pandey, Lead Data Analyst  
> **Target Audience:** Engineering Leads, BI Developers, Quality Assurance, and Leadership  
> **Scope:** Deep-dive Root Cause Analyses (RCA) on data pipeline defects, UI filter discrepancies, macroeconomic policy anomalies, and seasonality dynamics.

---

## 📋 RCA Incident Summary Log

| Incident ID | Severity | Category | Title / Summary | Status |
|:---:|:---:|:---|:---|:---:|
| **RCA-01** | **Critical (P1)** | DAX Formula Defect | Reference DAX `2024 Revenue` filtered on FY2023, causing false 0% revenue growth | **RESOLVED** |
| **RCA-02** | **Medium (P2)** | UI State Discrepancy | Dashboard Top 3 Makers visual numbers differed from single-year raw totals | **RESOLVED** |
| **RCA-03** | **Business (P3)** | Macroeconomic Anomaly | Investigation of negative penetration states and post-subsidy dip (P3) | **DOCUMENTED** |
| **RCA-04** | **Business (P4)** | Seasonal Variance | Underlying drivers of March/November EV sales spikes vs. June troughs (P8) | **DOCUMENTED** |

---

## 🔍 Incident RCA-01: Reference DAX Measure Copy-Paste Bug (Defect D1)

### 1. Problem Statement & Symptom
When calculating the revenue growth between FY2023 and FY2024 to answer primary business question **P10**, the formula `Revenue Growth Rate 2023-2024` evaluated to **0.00%**, despite EV sales unit volume growing from 727,903 units to 932,692 units in 2-Wheelers (+28.1%) and 47,465 units to 86,901 units in 4-Wheelers (+83.1%).

### 2. Root Cause Analysis (5 Whys)
1. **Why was revenue growth 0%?**  
   The numerator `[2024 Revenue] - [2023 Revenue]` evaluated to exactly `0`.
2. **Why was `[2024 Revenue]` equal to `[2023 Revenue]`?**  
   Both measures returned the exact same value of ₹14,398.78 Crores.
3. **Why did `[2024 Revenue]` return FY2023 revenue?**  
   The measure definition in `DAX_Measures_And_Calculated_Columns_AtliQ_Motors.xlsx` had the filter argument hardcoded to `dim_date[fiscal_year] = 2023`.
4. **Why was `fiscal_year = 2023` present in `2024 Revenue`?**  
   A copy-paste error occurred during initial metric drafting: `2023 Revenue` was duplicated to create `2024 Revenue`, the measure title was updated, but the internal filter context was never modified.
5. **Why was this critical?**  
   If shipped without audit, leadership would have been informed that AtliQ Motors' addressable market experienced zero revenue expansion in FY2024, leading to incorrect market entry decisions.

### 3. Technical Comparison

```dax
-- AS SUPPLIED (Defective):
2024 Revenue = 
CALCULATE(
    SUMX(
        'electric_vehicle_sales_by_makers',
        'electric_vehicle_sales_by_makers'[electric_vehicles_sold]
            * LOOKUPVALUE('Revenue'[Average Price], 'Revenue'[Vehicle_category], 'electric_vehicle_sales_by_makers'[vehicle_category])
    ),
    dim_date[fiscal_year] = 2023          -- ROOT CAUSE: Hardcoded to 2023
)

-- CORRECTED VERSION (Implemented):
2024 Revenue = 
CALCULATE(
    SUMX(
        'electric_vehicle_sales_by_makers',
        'electric_vehicle_sales_by_makers'[electric_vehicles_sold]
            * LOOKUPVALUE('Revenue'[Average Price], 'Revenue'[Vehicle_category], 'electric_vehicle_sales_by_makers'[vehicle_category])
    ),
    dim_date[fiscal_year] = 2024          -- RESOLVED: Filtered on 2024
)
```

### 4. Remediation & Impact
- **Financial Parity Restored:**
  - FY2022 Revenue: **₹5,312.28 Cr**
  - FY2023 Revenue: **₹14,398.78 Cr**
  - FY2024 Revenue (Corrected): **₹22,362.07 Cr** (previously ₹14,398.78 Cr)
  - True FY23➔FY24 Revenue Growth: **+55.31%** (was 0.00%)
  - True FY22➔FY24 Revenue Growth: **+320.95%**
- **Automated Prevention:** Implemented mathematical assertion checks in [`scripts/test_pipeline_assertions.py`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/scripts/test_pipeline_assertions.py) to prevent regression.

---

## 🔍 Incident RCA-02: Dashboard Walkthrough Filter-State Discrepancy (D2)

### 1. Problem Statement & Symptom
In the reference dashboard walkthrough GIF (`AtliQ_Car_Services_gif.gif`), the "Top 3 Makers" visual displayed:
- `OLA ELECTRIC`: **475K**
- `TVS`: **263K**
- `ATHER`: **184K**

However, an initial independent calculation of raw FY2024 sales showed:
- `OLA ELECTRIC`: **322,489** (322K)
- `TVS`: **180,743** (181K)
- `ATHER`: **107,552** (108K)

And all-time (FY22+FY23+FY24) totals showed:
- `OLA ELECTRIC`: **489,473** (489K)
- `TVS`: **272,575** (273K)
- `ATHER`: **204,449** (204K)

Neither matched the displayed 475K / 263K / 184K cards.

### 2. Forensic Investigation & Discovery
To determine the root cause, a combinatorial query was executed across all possible single and multi-year slicer configurations:

```python
# Multi-year summation analysis
fy23_24_ola = 152583 (FY23) + 322489 (FY24) = 475,072  -> Rounds to 475K (EXACT MATCH)
fy23_24_tvs = 82093  (FY23) + 180743 (FY24) = 262,836  -> Rounds to 263K (EXACT MATCH)
fy23_24_ath = 76921  (FY23) + 107552 (FY24) = 184,473  -> Rounds to 184K (EXACT MATCH)
```

### 3. Root Cause
The default visual display in the walkthrough GIF was captured with the `fiscal_year` slicer filtered to **FY2023 and FY2024 simultaneously** (excluding FY2022).

### 4. Resolution & Reporting Standard
- For answering **Question P1** (which specifically mandates evaluating FY2023 and FY2024 separately), the single-year audited figures were presented:
  - **FY2023 Top 3:** OLA ELECTRIC (152,583), OKINAWA (96,945), HERO ELECTRIC (88,993)
  - **FY2024 Top 3:** OLA ELECTRIC (322,489), TVS (180,743), ATHER (107,552)
- Added explicit documentation in [`docs/RESULTS.md`](file:///g:/Data%20Analytics/19.Portfolio/atliq-motors-insights/docs/RESULTS.md#P1) explaining the multi-year UI filter state to eliminate reviewer confusion.

---

## 🔍 Incident RCA-03: Investigation of Negative Penetration Rates (Question P3)

### 1. Problem Statement
Primary question **P3** asked: *"List down the states that have shown a negative penetration rate change from FY2022 to FY2024."*

### 2. Finding & Anomaly
A complete SQL query comparing `Penetration Rate 2024 - Penetration Rate 2022` across all 35 states and UTs revealed that **0 states had a negative 2-year change** (every single state increased its EV penetration rate between FY22 and FY24).

### 3. Granular Root Cause Analysis (YoY Disaggregation)
By breaking down the 2-year period into individual annual steps (**FY22➔FY23** and **FY23➔FY24**), a critical macroeconomic trend was uncovered:
- **FY22➔FY23:** All states experienced positive penetration growth.
- **FY23➔FY24:** Exactly **6 states experienced an adoption contraction**:

| State | FY2023 Penetration | FY2024 Penetration | YoY Change (FY23➔FY24) |
|:---|:---:|:---:|:---:|
| **Rajasthan** | 3.51% | 2.97% | **-0.54%** |
| **Haryana** | 3.12% | 2.82% | **-0.30%** |
| **Uttarakhand** | 3.65% | 3.42% | **-0.23%** |
| **Gujarat** | 4.88% | 4.71% | **-0.17%** |
| **Jharkhand** | 2.37% | 2.29% | **-0.08%** |
| **Himachal Pradesh** | 1.84% | 1.77% | **-0.07%** |

### 4. Macroeconomic Drivers
1. **FAME-II Central Subsidy Slashes (June 1, 2023):** The Ministry of Heavy Industries reduced the electric 2-wheeler subsidy cap from **40% of ex-factory price to 15%**, increasing average retail prices by ₹20,000–₹35,000 per vehicle overnight.
2. **State-Level Budget Expiry:** Rajasthan and Gujarat exhausted their state-specific direct purchase subsidy funds by Q2 FY2024, compounding the central price hike.
3. **Price Sensitivity in Non-Coastal States:** Unlike Kerala and Goa (which have high per capita GDP and continuous local tax waivers), Northern/Central commuter markets showed severe price elasticity.

---

## 🔍 Incident RCA-04: Seasonal Sales Concentration Dynamics (Question P8)

### 1. Problem Statement
Monthly EV unit aggregation identified extreme variance across the calendar year:
- **All-Time Peak:** **March (291,587 units)** — 2.73x the volume of the lowest month.
- **Secondary Peak:** **November (205,196 units)**.
- **All-Time Trough:** **June (106,709 units)** and **July (127,426 units)**.

### 2. Root Cause Breakdown

```
  High Sales ──► [March Peak: 291.6K]           [November Peak: 205.2K]
                  • Section 32 Tax Write-off       • Festive Diwali / Dhanteras
                  • OEM Financial Year-End Targets • Auspicious Buying Window
                  
   Low Sales ──► [June Trough: 106.7K]           [July Trough: 127.4K]
                  • Post-March Demand Pull-Forward • Monsoon Pre-Season Lull
                  • Q1 Inventory Depletion         • FAME-II Subsidy Reset (2023)
```

1. **March Spike Drivers (Financial Year-End):**
   - **Commercial EV Accelerated Depreciation:** Under Section 32 of the Indian Income Tax Act, corporate entities, commercial fleets, and proprietary businesses can claim **40% accelerated tax depreciation** on electric vehicles registered before March 31.
   - **OEM Year-End Dealer Push:** Manufacturers and dealerships offer aggressive discounts to clear fiscal-year inventory quotas.
2. **November Spike Drivers (Festive Season):**
   - **Diwali & Dhanteras:** Cultural propensity to make major asset purchases during festive auspicious periods.
3. **June/July Trough Drivers:**
   - **Demand Exhaustion:** Q4 FY-end purchasing pulls forward demand from Q1 of the following fiscal year.
   - **Monsoon Onset:** Slower retail showroom footfall during peak Indian monsoon months.

---

## 🛡 Systemic Learnings & Preventive Controls

1. **Mandatory Automated SQL/DAX Assertions:** Never rely solely on spreadsheet documentation without cross-verifying calculation engines against raw relational tables.
2. **UI Slicer State Logging:** When capturing visuals for documentation or reports, always record the exact active slicer filter state in visual metadata.
3. **Multi-Horizon Trend Analysis:** Two-year CAGR numbers can mask intermediate macro volatility; always audit annual delta steps alongside multi-year aggregates.
