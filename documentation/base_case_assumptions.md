# Base Case Assumptions — Aster Deepwater Field

**Document status:** Proposed illustrative baseline — pending validation
**Model version:** 1.0
**Currency:** Constant 2026 USD
**Economic scope:** Preliminary, pre-tax, unlevered project economics
**Evaluation horizon:** 25 project years
**Valuation date:** Beginning of Project Year 1

---

## 1. Purpose

This document defines the initial numerical assumptions for comparing two
fictional offshore field development concepts:

1. Subsea Tieback
2. Standalone Floating Production, Storage, and Offloading (FPSO)

The assumptions provide a consistent reference for synthetic data generation,
production forecasting, capital and operating expenditure modeling, annual
cash flow calculations, investment indicators, sensitivity analysis, and
Power BI reporting.

All values are illustrative modeling inputs. They do not represent a real
field, operator estimate, approved development plan, or investment recommendation.

## 2. Modeling principles

- All monetary amounts are expressed in constant 2026 USD.
- Production volumes are expressed in barrels of oil (bbl).
- Production rates are expressed in barrels of oil per day (bbl/day).
- The model uses annual time steps.
- The initial model is pre-tax and unlevered.
- Financing costs, debt service, royalties, production-sharing terms, income
  taxes, inflation, and foreign-exchange effects are excluded.
- No terminal value is assumed.
- Capital expenditure is modeled explicitly by project year.
- Operating expenditure is separated into fixed costs, variable costs,
  and host-facility tariff where applicable.
- Abandonment expenditure is modeled separately from routine operating costs.
- Production and economic assumptions must pass validation before investment
  indicators are accepted as final.
- Scenario results must not be presented as actual field economics.

## 3. Development concept assumptions

| Parameter | Subsea Tieback | Standalone FPSO |
|---|---:|---:|
| First oil year | 3 | 4 |
| Maximum production capacity (bbl/day) | 60,000 | 100,000 |
| Initial production ramp factor | 60% | 60% |
| Second production-year ramp factor | 85% | 85% |
| Plateau production factor | 100% | 100% |
| Plateau duration | 5 years | 5 years |
| Annual decline after plateau | 8% | 8% |
| Production uptime factor | 90% | 90% |
| Evaluation horizon | 25 years | 25 years |

### 3.1 Production profile logic

Production is zero before the first-oil year.

For the first production year, the modeled production rate is 60% of maximum
capacity. In the second production year, it increases to 85%. The production
factor reaches 100% in the third production year and remains at plateau for
five production years, including that third year.

After the five-year plateau period, production declines by 8% annually.

The annual production calculation is:

Annual Oil Production (bbl) =
Maximum Production Capacity (bbl/day)
x Production Profile Factor
x Uptime Factor
x Annual Production Days

For this initial model, annual production days are 365.

The uptime factor is applied separately from the production profile factor.
The resulting production volume must never exceed the annual volume implied
by maximum capacity, uptime, and annual production days.

Production is zero after the evaluation horizon.

## 4. Oil price scenarios

| Scenario | Oil Price (USD/bbl) | Status |
|---|---:|---|
| Low | 55 | Proposed illustrative assumption |
| Base | 75 | Proposed illustrative assumption |
| High | 95 | Proposed illustrative assumption |

The initial model uses constant real oil prices within each scenario.
Oil price does not escalate with time.

The same oil-price scenario must be applied consistently to both development
concepts when comparing their economics.

## 5. Discount rate

| Parameter | Value | Unit |
|---|---:|---|
| Annual discount rate | 10% | Decimal: 0.10 |

The discount rate is a proposed illustrative assumption, not a company-approved
hurdle rate or a validated estimate of the cost of capital.

The model will calculate NPV at the beginning of Project Year 1 using an
end-of-year cash flow convention. Project Year 1 cash flows are discounted
by one annual period; Project Year 0 cash flows, if introduced later, are
undiscounted.

The discount rate must be configurable for sensitivity analysis.

## 6. Capital expenditure assumptions

The following development capital expenditure schedule is a proposed synthetic
baseline. Amounts are in USD millions.

### 6.1 Subsea Tieback

| Project Year | CAPEX (USD million) | Illustrative activity |
|---|---:|---|
| 1 | 250 | Engineering and early development |
| 2 | 750 | Subsea infrastructure and installation |
| 3 | 300 | Completion, tie-in, and commissioning |
| 4-25 | 0 | No additional development CAPEX assumed in the base case |
| **Total** | **1,300** | |

### 6.2 Standalone FPSO

| Project Year | CAPEX (USD million) | Illustrative activity |
|---|---:|---|
| 1 | 400 | Engineering and early project expenditure |
| 2 | 1,000 | Long-lead equipment and development |
| 3 | 1,500 | FPSO construction and subsea development |
| 4 | 1,100 | Installation, commissioning, and start-up |
| 5-25 | 0 | No additional development CAPEX assumed in the base case |
| **Total** | **4,000** | |

These schedules are deliberately simplified. They do not model cost escalation,
contingency drawdown, phased expansion, or future reinvestment.

All CAPEX must be represented by project year in the economic model rather
than spread uniformly across the evaluation horizon.

## 7. Operating expenditure assumptions

All values below are proposed illustrative assumptions.

### 7.1 Subsea Tieback

| Cost component | Assumption | Unit |
|---|---:|---|
| Fixed operating expenditure | 35,000,000 | USD per producing year |
| Variable operating expenditure | 8 | USD/bbl |
| Host-facility tariff | 12 | USD/bbl |
| Abandonment expenditure | 150,000,000 | USD |

The host-facility tariff represents a simplified illustrative charge for
processing or transporting production through an existing host facility.
It is applied to produced oil volumes and is separate from variable operating
expenditure.

### 7.2 Standalone FPSO

| Cost component | Assumption | Unit |
|---|---:|---|
| Fixed operating expenditure | 120,000,000 | USD per producing year |
| Variable operating expenditure | 6 | USD/bbl |
| Host-facility tariff | 0 | USD/bbl |
| Abandonment expenditure | 350,000,000 | USD |

The standalone FPSO concept has no host-facility tariff in this simplified
model. Its fixed and variable operating costs are modeled independently.

### 7.3 Operating cost calculation

For each concept and producing year:

Variable OPEX = Annual Oil Production x Variable OPEX Rate

Host Tariff = Annual Oil Production x Host Tariff Rate

Routine OPEX = Fixed OPEX + Variable OPEX + Host Tariff

Fixed OPEX applies in producing years only in the initial model.

No routine operating expenditure is incurred before first oil or after the
last producing year. Abandonment expenditure is recorded separately in
Project Year 25.

This convention is a simplifying model assumption, not a statement about
how costs would necessarily occur in an actual offshore project.

## 8. Abandonment and end-of-life convention

Abandonment expenditure is recorded in Project Year 25:

- Subsea Tieback: USD 150 million
- Standalone FPSO: USD 350 million

These are proposed synthetic assumptions. The model does not yet include
salvage value, asset resale proceeds, residual value, or tax effects.

The abandonment cost must appear once per development concept, not once per
well or production record.

## 9. Revenue and annual cash flow

Annual revenue is calculated as:

Revenue = Annual Oil Production x Oil Price

The initial pre-tax, unlevered annual project cash flow is:

Net Project Cash Flow =
Revenue
- CAPEX
- Routine OPEX
- Abandonment Expenditure

No income tax, royalties, production-sharing payments, financing costs, or
working-capital movements are included in this initial definition.

Cumulative undiscounted cash flow is the running sum of annual net project
cash flow.

## 10. Economic indicators

The model is intended to calculate the following indicators for each
development concept and oil-price scenario:

- Total oil production (bbl)
- Total revenue (USD)
- Total CAPEX (USD)
- Total routine OPEX (USD)
- Total host-facility tariff (USD)
- Total abandonment expenditure (USD)
- Total net project cash flow (USD)
- Annual and cumulative cash flow
- Net Present Value (NPV)
- Internal Rate of Return (IRR), where a meaningful solution exists
- Undiscounted payback period, where achieved
- Discounted payback period, where achieved
- Breakeven oil price, defined as the constant real oil price that produces
  NPV = 0 under the stated model assumptions

NPV and IRR must not be calculated from incomplete or unvalidated economic
inputs.

If a concept does not achieve payback within the evaluation horizon, report
that payback was not achieved rather than extrapolating an unsupported date.

If cash flows do not support a meaningful IRR solution, report the result as
undefined or not available. Do not force an IRR value.

## 11. Sensitivity analysis

The initial sensitivity framework will evaluate:

1. Oil price: USD 55, 75, and 95 per barrel.
2. Discount rate: alternative rates around the 10% base assumption.
3. Development CAPEX: percentage increases and decreases from the base case.
4. Fixed OPEX: percentage increases and decreases from the base case.
5. Variable OPEX: alternative per-barrel cost assumptions.
6. Production performance: changes to plateau capacity and decline rate.
7. First-oil timing: delays relative to the base schedule.

Sensitivity ranges must be documented before their results are interpreted.
They are scenario tests, not probability distributions or forecasts.

## 12. Required validation controls

Before economic results are approved for reporting, automated QA must verify:

- Every required assumption has a defined value and unit.
- No pending placeholder is silently interpreted as a genuine zero cost.
- Production is zero before first oil.
- Production factors follow the specified ramp, plateau, and decline logic.
- Annual production does not exceed modeled capacity.
- Production volumes and cash flow calculations reconcile independently.
- CAPEX schedules reconcile to their stated totals.
- Fixed OPEX applies only in producing years under the initial convention.
- Variable OPEX and host tariff reconcile to their respective rates and volumes.
- Abandonment expenditure occurs once in Project Year 25.
- No production or cash flow records fall outside the evaluation horizon.
- Annual cash flow reconciles to revenue less CAPEX, routine OPEX, and
  abandonment expenditure.
- NPV calculations reconcile to independently calculated discounted cash flow.
- Breakeven price is validated by confirming that NPV is approximately zero
  at the calculated price.
- The two development concepts are evaluated using the same oil-price
  scenario, discount-rate convention, and evaluation horizon.

## 13. Limitations

This is a simplified conceptual comparison, not a field-development feasibility
study or investment-grade economic evaluation.

The model excludes, among other items:

- Fiscal regimes, royalties, and production-sharing agreements
- Income tax and depreciation
- Financing structure and debt service
- Inflation and cost escalation
- Gas production and gas monetization
- Detailed reservoir simulation
- Well-level drilling and completion schedules
- Construction risk and probabilistic cost estimates
- Decommissioning timing beyond the stated simplified convention
- Salvage value and residual asset value
- Uncertainty distributions and probabilistic risk analysis

The proposed CAPEX, OPEX, tariff, abandonment, production, oil-price, and
discount-rate assumptions must be treated as synthetic until validated
against the intended educational modeling scope.

## 14. Approval status and next steps

**Status: Proposed illustrative baseline — not yet approved for economic results.**

Before generating production profiles or calculating NPV, IRR, payback,
or breakeven price:

1. Review the assumptions in this document.
2. Reconcile the assumptions with `economic_assumptions.csv`.
3. Confirm that all cost placeholders are resolved or explicitly classified
   as not applicable.
4. Implement an independent validation script.
5. Generate the annual production and CAPEX schedules.
6. Reconcile production and cost schedules before building annual cash flows.
7. Record the validation outcome in the project QA documentation.

This document is the proposed reference for the initial synthetic base case.
Any approved changes must be reflected consistently in the assumptions
register, generation scripts, economic engine, validation tests, and reports.
