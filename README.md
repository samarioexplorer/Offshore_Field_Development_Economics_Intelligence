
# Offshore Field Development & Economics Intelligence

## 1. Project Overview

**Offshore Field Development & Economics Intelligence** is an end-to-end analytical portfolio project designed to evaluate and compare two illustrative offshore oil field development concepts:

* **Standalone FPSO** — a dedicated Floating Production, Storage, and Offloading development.
* **Subsea Tieback** — a subsea development connected to existing host infrastructure.

The project demonstrates how engineering assumptions, production forecasts, capital expenditure, operating costs, oil-price scenarios, and discounted cash-flow analysis can be integrated into a reproducible analytical workflow.

The solution combines:

* Python for synthetic data generation, economic calculations, and validation.
* Pandas and NumPy for data transformation and numerical analysis.
* SQLite for structured analytical storage.
* SQL views for analytical access and reconciliation.
* Power BI and DAX for interactive economic evaluation and executive reporting.
* Git and GitHub for version control and portfolio publication.

The objective is to demonstrate a complete engineering analytics workflow, from assumptions and data preparation through economic modeling, validation, and decision-oriented visualization.

> **Important disclaimer:** This is a synthetic, illustrative analytical case study. Development concepts, production profiles, costs, and economic outputs are model assumptions rather than verified estimates for an actual offshore asset. Results must not be interpreted as reserves estimates, sanctioned project budgets, investment recommendations, or forecasts of actual project performance.

---

## 2. Business and Engineering Objectives

The project addresses several questions relevant to offshore field development planning:

1. How do the standalone FPSO and subsea tieback concepts compare economically?
2. How do development timing and production capacity affect projected cash flow?
3. How do CAPEX and OPEX assumptions influence project economics?
4. How sensitive is project value to low, base, and high oil-price scenarios?
5. What are the differences in NPV, IRR, payback period, and breakeven oil price?
6. How is capital deployed relative to first oil?
7. How can engineering assumptions and economic results be reconciled across Python, SQLite, SQL, and Power BI?
8. How can the resulting analysis support transparent concept comparison without overstating the certainty of the model?

The project emphasizes traceable assumptions, consistent calculations, data integrity, and clear communication of economic results.

---

## 3. Development Concepts and Model Assumptions

The model compares two hypothetical offshore development configurations.

### 3.1 Concept assumptions

| Parameter                   | Standalone FPSO | Subsea Tieback |
| --------------------------- | --------------: | -------------: |
| First-oil timing            |          Year 4 |         Year 3 |
| Nominal production capacity | 100,000 bbl/day | 60,000 bbl/day |
| Uptime assumption           |             90% |            90% |
| Total development CAPEX     |    $4.0 billion |   $1.3 billion |
| Annual fixed OPEX           |    $120 million |    $35 million |
| Variable OPEX               |          $6/bbl |         $8/bbl |
| Host processing tariff      |     Not modeled |        $12/bbl |
| Abandonment cost            |    $350 million |   $150 million |

These values are illustrative model inputs, not externally verified estimates for a specific field or development project.

### 3.2 Economic assumptions

| Parameter               | Assumption            |
| ----------------------- | --------------------- |
| Low oil-price scenario  | $55/bbl               |
| Base oil-price scenario | $75/bbl               |
| High oil-price scenario | $95/bbl               |
| Discount rate           | 10%                   |
| Evaluation horizon      | 25 years              |
| Currency basis          | Constant 2026 USD     |
| Economic basis          | Pre-tax and unlevered |
| Calendar convention     | 365 days per year     |

The assumptions establish a consistent basis for comparing the two development concepts. They do not represent a complete field-development feasibility study.

### 3.3 Illustrative production profile

The production model uses a simplified production profile:

* First production year: 60% of nominal capacity.
* Second production year: 85% of nominal capacity.
* Following five producing years: full-capacity plateau.
* Subsequent production: 8% annual decline.
* Uptime: 90%.

Annual production is calculated as:

`Annual Production = Capacity × Production Profile Factor × Uptime × 365`

The production profile is a simplified modeling assumption. It does not incorporate reservoir simulation, well-by-well decline behavior, drilling schedules, detailed maintenance plans, or other field-specific constraints.

---

## 4. Economic Methodology

The analytical workflow calculates annual production, development expenditure, operating expenditure, revenue, and project cash flow for each development concept.

### 4.1 Core economic metrics

**Net Present Value (NPV)**

NPV is calculated by discounting the modeled project cash flows at the specified discount rate. It provides a common basis for comparing the economic value of the two concepts.

**Internal Rate of Return (IRR)**

IRR represents the discount rate at which modeled project NPV equals zero. Where cash-flow patterns produce multiple IRR roots or an ambiguous result, a single IRR is not reported as though it were unambiguous.

**Payback period**

The model evaluates the time required for cumulative project cash flow to recover the initial investment. Undiscounted and discounted payback are distinguished.

**Breakeven oil price**

The breakeven calculation identifies the oil price at which modeled project NPV equals zero under the specified assumptions.

**Scenario sensitivity**

Low-, base-, and high-price cases quantify how the assumed oil-price environment affects modeled project economics.

These calculations are conditional on the model's inputs, cash-flow timing, and economic conventions.

---

## 5. Illustrative Base-Case Results

The following results are from the project's synthetic model outputs.

| Economic metric         | Standalone FPSO | Subsea Tieback |
| ----------------------- | --------------: | -------------: |
| Base-case NPV at 10%    |  $7.729 billion | $4.797 billion |
| Base-case IRR           |          39.62% |         62.44% |
| Undiscounted payback    |      6.44 years |     4.77 years |
| Discounted payback      |      6.91 years |     5.01 years |
| Breakeven oil price     |      $29.11/bbl |     $32.03/bbl |
| Cumulative production   |    481.50 MMbbl |   294.09 MMbbl |
| Total development CAPEX |    $4.0 billion |   $1.3 billion |

### 5.1 Interpretation

Under the model's base-case assumptions:

* The standalone FPSO generates the larger absolute NPV and cumulative production volume.
* The subsea tieback requires less initial development capital.
* The subsea tieback has a higher modeled IRR and a shorter payback period.
* The standalone FPSO has the lower modeled breakeven oil price.

These results illustrate the trade-offs between absolute project value, capital intensity, production scale, and investment efficiency.

They do not establish that either concept is universally superior. A real development decision would also require reservoir uncertainty analysis, engineering feasibility, host capacity, infrastructure availability, fiscal terms, financing, environmental requirements, execution risk, and other asset-specific considerations.

---

## 6. Oil-Price Scenario Analysis

The model evaluates three oil-price assumptions: $55/bbl, $75/bbl, and $95/bbl.

### 6.1 Scenario NPV results

| Development concept |  Low-price NPV | Base-price NPV |  High-price NPV |
| ------------------- | -------------: | -------------: | --------------: |
| Standalone FPSO     | $4.361 billion | $7.729 billion | $11.098 billion |
| Subsea Tieback      | $2.564 billion | $4.797 billion |  $7.029 billion |

The values above are the model's recorded outputs and are rounded for presentation.

### 6.2 Scenario interpretation

The scenario results demonstrate how oil-price assumptions affect modeled project value.

Both concepts have positive NPV across the three specified scenarios under the modeled assumptions. The absolute change in NPV between the low and base cases, and between the base and high cases, is approximately symmetric in the model.

This sensitivity should not be interpreted as a complete measure of investment risk. The analysis does not replace probabilistic uncertainty modeling or a comprehensive assessment of technical, commercial, fiscal, and execution risks.

**IRR reporting limitation:** Some modeled low-price cash-flow cases have multiple IRR roots. In those cases, a single scalar IRR is left blank rather than presenting a potentially misleading result. NPV at the specified discount rate remains an important complementary metric.

---

## 7. Development CAPEX and Execution Timing

The model includes annual development CAPEX schedules for both concepts.

### Standalone FPSO

| Project year    |                  CAPEX |
| --------------- | ---------------------: |
| Year 1          |           $400 million |
| Year 2          |           $1.0 billion |
| Year 3          |           $1.5 billion |
| Year 4          |           $1.1 billion |
| **Total** | **$4.0 billion** |

### Subsea Tieback

| Project year    |                  CAPEX |
| --------------- | ---------------------: |
| Year 1          |           $250 million |
| Year 2          |           $750 million |
| Year 3          |           $300 million |
| **Total** | **$1.3 billion** |

The report also evaluates CAPEX deployment relative to first oil, cumulative CAPEX, and cumulative net project cash flow.

This supports an execution-oriented comparison of investment timing, capital accumulation, and the transition from development spending to production and cash generation.

The schedules are simplified illustrative profiles. They are not procurement schedules, sanctioned budgets, or execution plans for an actual development.

---

## 8. Power BI Executive Report

The completed Power BI report is organized into four analytical pages.

### Page 1 — Development Concept Evaluation

Provides the executive comparison of the two development concepts.

Key analytical themes include:

* Development concept comparison.
* First-oil timing and production capacity.
* CAPEX and investment requirements.
* Base-case economic performance.
* NPV-to-CAPEX investment efficiency.
* High-level decision support.

### Page 2 — Production Forecast

Examines the modeled production profiles over the evaluation horizon.

Key analytical themes include:

* Annual production.
* Cumulative oil production.
* Production profile by development concept.
* Plateau and decline assumptions.
* Comparison of production scale and timing.

### Page 3 — Development Economics & Scenario Analysis

Focuses on modeled economic outcomes and sensitivity to oil-price assumptions.

Key analytical themes include:

* NPV and IRR.
* Payback and breakeven metrics.
* Low-, base-, and high-price scenarios.
* Comparative investment economics.
* Scenario-driven changes in project value.

### Page 4 — Development Lifecycle & Execution Strategy

Examines the relationship between development expenditure, first oil, and project cash flow.

Key analytical themes include:

* Annual development CAPEX.
* CAPEX deployment relative to first oil.
* Cumulative CAPEX.
* Cumulative net project cash flow.
* First-oil timing and preproduction periods.
* Evaluation horizon and execution profile.

All report pages should retain a clear disclaimer that the results are based on a synthetic illustrative model.

**Power BI artifact:** `powerbi/Offshore_Field_Development_Economics_Intelligence.pbix`

---

## 9. Data Architecture and Technology Stack

The project uses a layered analytical workflow.

### 9.1 Python analytical layer

Python supports the generation, preparation, calculation, and validation of the model's data.

Core technologies:

* Python
* Pandas
* NumPy

The Python layer establishes the assumptions and calculated outputs used throughout the project.

### 9.2 SQLite data layer

SQLite provides a local analytical database containing the model's structured data and registered analytical views.

**Database:** `database/offshore_field_development_economics.db`

The database supports inspection, querying, reconciliation, and downstream reporting.

### 9.3 SQL analytical layer

Six analytical views have been identified in the SQLite database:

| View                                  | Purpose                                              |
| ------------------------------------- | ---------------------------------------------------- |
| `vw_Annual_Production_Summary`      | Annual and cumulative production analysis            |
| `vw_Annual_Economics_Summary`       | Access to annual economic results                    |
| `vw_Base_Investment_Comparison`     | Base investment metrics                              |
| `vw_Scenario_Investment_Comparison` | Scenario investment metrics                          |
| `vw_Scenario_NPV_Comparison`        | Low-, base-, and high-price NPV comparison           |
| `vw_Scenario_Cash_Flow_Profile`     | Scenario cash-flow and discounted cash-flow analysis |

The views provide structured access to production, economics, investment metrics, and scenario outputs.

These are views registered in the SQLite database. Their presence does not necessarily mean that each view has a separate corresponding `.sql` file in the repository.

### 9.4 Power BI semantic and presentation layer

Power BI provides the executive reporting interface for comparing development concepts and examining production, economics, scenario sensitivity, and capital deployment.

DAX measures support the presentation and analysis of model outputs. The report is intended to make the assumptions and their implications easier to interpret, rather than replace the underlying engineering calculations.

### 9.5 Version control

Git and GitHub support version history, documentation, and portfolio publication.

**Repository:** `samarioexplorer/Offshore_Field_Development_Economics_Intelligence`

---

## 10. Quality Assurance and Reconciliation

Validation is a core component of the project.

The workflow has included checks covering:

* Economic assumption consistency.
* Production profile calculations.
* Annual production and cumulative production.
* CAPEX schedule reconciliation.
* Operating costs and revenue calculations.
* Cash-flow calculations.
* NPV and investment metric calculations.
* Oil-price scenario outputs.
* SQLite database and analytical views.
* SQL-to-Python reconciliation.
* Power BI measure and visual consistency.

Recorded project validation history includes **205 passing checks: 190 core-model checks and 15 SQL-view QA checks**.

This is a record of the project's validation runs, not a claim that every possible input, edge case, visual interaction, or future modification has been tested. Changes to calculations, database objects, or report measures should be followed by appropriate regression checks.

The SQL scenario NPV comparison view has also been inspected directly. Its expected output columns were confirmed, and a query returned the two development concepts with low-, base-, and high-price NPV values consistent with the model's recorded results.

---

## 11. Repository Structure

The principal project artifacts are organized around data, the analytical database, Python, SQL, documentation, and Power BI.

```text
Offshore_Field_Development_Economics_Intelligence/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── database/
│   └── offshore_field_development_economics.db
│
├── documentation/
│
├── powerbi/
│   └── Offshore_Field_Development_Economics_Intelligence.pbix
│
├── python/
│   ├── generation/
│   ├── preparation/
│   └── validation/
├── sql/
├── presentation/
│
├── README.md
└── LICENSE
```

This is a high-level representation of the project's principal directories and artifacts. It is not intended to enumerate every file. The actual repository contents should be used as the authoritative reference for the current file structure.

---

## 12. Reproducibility and Usage

To inspect the project:

1. Clone or download the repository.
2. Review this README and the documented economic assumptions.
3. Inspect the Python scripts and validation workflow.
4. Open the SQLite database with a compatible SQLite client or Python's `sqlite3` module.
5. Query the registered analytical views.
6. Open the Power BI report in Power BI Desktop.
7. Review the concept comparison, production forecast, economic scenarios, and development lifecycle pages.
8. Run the applicable validation scripts after changing assumptions or calculations.

A local Python installation and the project's required packages are necessary to execute the Python workflow. Power BI Desktop or a compatible Power BI environment is required to inspect the `.pbix` report.

The exact commands for reproducing the workflow should follow the scripts and dependencies actually present in the repository.

---

## 13. Limitations and Appropriate Use

This project is an engineering analytics portfolio case study.

It is not:

* A reserves certification.
* A reservoir simulation.
* A detailed field-development plan.
* A feasibility study for a real offshore asset.
* A sanctioned CAPEX or OPEX estimate.
* A fiscal or tax model.
* A probabilistic investment-risk assessment.
* A substitute for engineering, commercial, regulatory, or investment due diligence.

The results depend on simplified production profiles, assumed costs, defined oil-price scenarios, and the specified economic conventions.

Actual development decisions require asset-specific subsurface information, engineering design, cost estimates, commercial agreements, fiscal terms, environmental assessments, and uncertainty analysis.

---

## 14. Project Status

The project has progressed from model definition and synthetic data generation through economic calculations, SQLite analytical storage, SQL analysis, validation, and Power BI reporting.

The principal portfolio deliverables are:

* Documented development concepts and economic assumptions.
* Synthetic annual production profiles.
* CAPEX, OPEX, revenue, and project cash-flow calculations.
* NPV, IRR, payback, and breakeven calculations.
* Low-, base-, and high-price scenario analysis.
* SQLite analytical database and registered views.
* SQL-to-Python reconciliation and validation workflows.
* Four-page Power BI executive report.
* Project documentation and GitHub repository.

Further changes should be treated as controlled refinements and validated before being considered final.

---

## 15. Portfolio Value

This project demonstrates an integrated approach to offshore development economics and analytics, combining:

* Engineering-oriented assumptions.
* Production and cash-flow modeling.
* Capital deployment analysis.
* Economic evaluation and scenario sensitivity.
* Structured SQL data access.
* Automated validation and reconciliation.
* Power BI semantic modeling and executive reporting.
* Reproducible, documented analytical workflows.

The emphasis is on analytical traceability, engineering logic, transparent assumptions, and decision-oriented communication.
