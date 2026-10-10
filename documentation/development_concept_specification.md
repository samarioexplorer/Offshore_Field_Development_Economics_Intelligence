# Aster Deepwater Field — Development Concept Specification

## 1. Purpose

This document defines the initial modeling conventions for comparing
two fictional offshore oil development concepts.

All values are synthetic and illustrative. They do not represent an
actual discovery, operator, approved development plan, or investment
recommendation.

## 2. Development Concepts

### Concept A — Subsea Tieback

A fictional subsea oil development connected to an assumed existing
host facility.

The model may include:
- Subsea wells and completions
- Subsea infrastructure
- Tie-in and installation expenditure
- Host-facility operating costs
- A separately identified host-facility tariff, if applicable
- Capacity constraints and development timing

### Concept B — Standalone FPSO

A fictional offshore oil development supported by a dedicated
Floating Production, Storage, and Offloading facility.

The model may include:
- Subsea wells and completions
- Subsea infrastructure
- FPSO-related development expenditure
- Installation and commissioning
- FPSO and field operating costs
- Facility capacity constraints and development timing

## 3. Production Model

Production will be modeled annually.

The model must explicitly define:
- First-oil timing
- Ramp-up profile
- Plateau production
- Production decline
- Facility production capacity
- Economic life

Annual production must not exceed the applicable annualized facility
capacity.

Production forecasts must be internally consistent with the selected
development concept and schedule.

## 4. Capital Expenditure

Development CAPEX will be allocated to explicit project years and
documented cost categories.

The sum of annual CAPEX must reconcile to the total modeled development
CAPEX for each development concept.

CAPEX assumptions will be documented before financial calculations
are enabled.

## 5. Operating Expenditure

Operating expenditure will distinguish:
- Fixed annual OPEX
- Variable OPEX per barrel
- Host-facility tariffs, where applicable
- Abandonment expenditure

The model must avoid double-counting costs between tariffs and other
operating expenditure categories.

## 6. Financial Conventions

- Currency: USD
- Economic basis: Pre-tax, unlevered project cash flow
- Production basis: Barrels of oil
- Oil price basis: USD per barrel
- Cash-flow frequency: Annual
- Valuation date: Beginning of Project Year 1
- Year 0 cash flows: Undiscounted
- Discounting: Annual
- Fiscal terms: Excluded from the initial model
- Financing: Excluded from the initial model

## 7. Economic Indicators

The model will calculate:
- Annual revenue
- Annual CAPEX
- Annual OPEX
- Annual net project cash flow
- Cumulative production
- Net Present Value (NPV)
- Internal Rate of Return (IRR), where mathematically meaningful
- Project breakeven oil price under the defined model assumptions

## 8. Sensitivity Analysis

The model will evaluate defined changes in:
- Oil price
- Development CAPEX
- Production volume
- Operating costs
- First-oil timing
- Discount rate

Scenario assumptions must be documented, and results must be reproducible.

## 9. Quality Assurance

The validation framework must test:
- Source schema and data types
- Production and capacity consistency
- CAPEX reconciliation
- OPEX reconciliation
- Revenue calculations
- Cash-flow reconciliation
- Independent NPV calculation
- IRR validity
- Breakeven price validation
- Scenario consistency

## 10. Current Status

This specification defines the initial modeling framework.
Detailed production, cost, schedule, and scenario assumptions remain
subject to definition and validation before economic results are
calculated.
