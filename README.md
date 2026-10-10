# Offshore Field Development & Economics Intelligence

## Project Overview

An end-to-end analytical portfolio project designed to evaluate
fictional offshore oil field development concepts using Python,
SQL, SQLite, and Power BI.

The project will compare a subsea tieback concept with a standalone
Floating Production, Storage, and Offloading (FPSO) development.

## Business Objective

Evaluate how production assumptions, development expenditure,
operating costs, commodity prices, and project timing influence
project cash flows and investment indicators.

## Planned Analytical Capabilities

- Synthetic data generation and validation
- Production profile modeling
- Capital expenditure and operating expenditure analysis
- Annual project cash flow modeling
- Net Present Value (NPV)
- Internal Rate of Return (IRR)
- Breakeven oil price
- Development scenario and sensitivity analysis
- SQL-based analytical data management
- Power BI executive reporting

## Technology Stack

- Python
- pandas
- NumPy
- SQLite
- SQL
- Power BI
- DAX
- Git

## Data Policy

The project will use synthetic data and documented assumptions.
It will not represent actual operator performance, a real field
development plan, or verified investment returns.

## Economic Scope

The initial model is intended for preliminary, pre-tax,
unlevered economic comparison. Fiscal terms, financing,
and other excluded assumptions will be documented explicitly.

## Project Status

### Completed

- Project definition and documented economic assumptions
- Synthetic annual production profiles for both development concepts
- Annual CAPEX, OPEX, revenue, and project cash-flow modeling
- NPV, IRR, payback, and breakeven oil-price calculations
- Low-, base-, and high-oil-price scenario analysis
- Automated validation of assumptions, production profiles, economics,
  investment metrics, and scenario outputs
- SQLite analytical database construction
- SQL-to-Python reconciliation
- Six SQL analytical views for production, economics,
  investment comparison, and scenario analysis

### Current Phase

Power BI source inventory, semantic model design, and executive
dashboard development.

All economic inputs are illustrative synthetic assumptions.
Results are not forecasts or investment recommendations for an
actual offshore field development.

## Planned Repository Structure

- `data/raw/` — authoritative synthetic source datasets
- `data/processed/` — reproducible prepared datasets
- `database/` — local SQLite database
- `python/generation/` — synthetic data generation
- `python/preparation/` — data preparation
- `python/analytics/` — analytical and economic calculations
- `python/validation/` — automated quality assurance
- `sql/` — SQL queries and analytical views
- `powerbi/` — Power BI deliverables
- `documentation/` — assumptions, data dictionary, and QA records
- `PowerPoint/` — executive and technical presentations
- `outputs/` — generated reports and temporary deliverables
