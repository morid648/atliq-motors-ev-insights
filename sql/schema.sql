-- =============================================================================
-- Database Schema: atliq_motors_ev_insights
-- PostgreSQL Relational DDL & Constraints
-- Pipeline: CSV -> PostgreSQL Staging/Relational Model -> Power BI Star Schema
-- Reference: architecture.md §1-§2, prd.md §2
-- =============================================================================

-- Drop tables if existing (in reverse dependency order)
DROP TABLE IF EXISTS electric_vehicle_sales_by_state CASCADE;
DROP TABLE IF EXISTS electric_vehicle_sales_by_makers CASCADE;
DROP TABLE IF EXISTS dim_revenue CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- -----------------------------------------------------------------------------
-- 1. Date Dimension Table (dim_date)
-- Grain: One record per month (36 months across FY2022 to FY2024)
-- Fiscal Year Convention: April 1 to March 31
-- -----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date DATE PRIMARY KEY,
    fiscal_year INT NOT NULL CHECK (fiscal_year IN (2022, 2023, 2024)),
    quarter VARCHAR(2) NOT NULL CHECK (quarter IN ('Q1', 'Q2', 'Q3', 'Q4'))
);

-- -----------------------------------------------------------------------------
-- 2. Revenue Dimension Table (dim_revenue)
-- Grain: One record per vehicle category (2 categories: 2-Wheelers, 4-Wheelers)
-- Note: Manually created modeling dimension; stores assumed average selling price (ASP)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_revenue (
    vehicle_category VARCHAR(20) PRIMARY KEY,
    average_price NUMERIC(12, 2) NOT NULL CHECK (average_price > 0)
);

-- -----------------------------------------------------------------------------
-- 3. EV Sales by Makers Fact Table (electric_vehicle_sales_by_makers)
-- Grain: date x vehicle_category x maker (816 rows)
-- -----------------------------------------------------------------------------
CREATE TABLE electric_vehicle_sales_by_makers (
    maker_sale_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    vehicle_category VARCHAR(20) NOT NULL,
    maker VARCHAR(100) NOT NULL,
    electric_vehicles_sold INT NOT NULL CHECK (electric_vehicles_sold >= 0),
    CONSTRAINT fk_makers_date FOREIGN KEY (date) 
        REFERENCES dim_date (date) ON DELETE RESTRICT,
    CONSTRAINT fk_makers_category FOREIGN KEY (vehicle_category) 
        REFERENCES dim_revenue (vehicle_category) ON DELETE RESTRICT
);

-- -----------------------------------------------------------------------------
-- 4. EV Sales by State Fact Table (electric_vehicle_sales_by_state)
-- Grain: date x state x vehicle_category (2,445 rows)
-- -----------------------------------------------------------------------------
CREATE TABLE electric_vehicle_sales_by_state (
    state_sale_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    state VARCHAR(100) NOT NULL,
    vehicle_category VARCHAR(20) NOT NULL,
    electric_vehicles_sold INT NOT NULL CHECK (electric_vehicles_sold >= 0),
    total_vehicles_sold INT NOT NULL CHECK (total_vehicles_sold >= electric_vehicles_sold),
    CONSTRAINT fk_state_date FOREIGN KEY (date) 
        REFERENCES dim_date (date) ON DELETE RESTRICT,
    CONSTRAINT fk_state_category FOREIGN KEY (vehicle_category) 
        REFERENCES dim_revenue (vehicle_category) ON DELETE RESTRICT
);

-- -----------------------------------------------------------------------------
-- Indexes for High-Performance Join and Aggregation Queries
-- -----------------------------------------------------------------------------
CREATE INDEX idx_makers_date ON electric_vehicle_sales_by_makers (date);
CREATE INDEX idx_makers_category ON electric_vehicle_sales_by_makers (vehicle_category);
CREATE INDEX idx_makers_maker ON electric_vehicle_sales_by_makers (maker);

CREATE INDEX idx_state_date ON electric_vehicle_sales_by_state (date);
CREATE INDEX idx_state_state ON electric_vehicle_sales_by_state (state);
CREATE INDEX idx_state_category ON electric_vehicle_sales_by_state (vehicle_category);
