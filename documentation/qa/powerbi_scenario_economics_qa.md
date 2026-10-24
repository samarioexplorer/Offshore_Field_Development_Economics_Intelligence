
# Power BI Scenario Economics — QA Report

## Project Information

**Project:** Offshore Field Development Economics Intelligence
**Component:** Power BI Semantic Model and Executive Dashboard
**QA Scope:** Oil-price scenario analysis, investment returns, and IRR presentation
**Status:** Targeted validation completed; final dashboard regression checks pending

---

## 1. Objective

Document the validation and remediation of scenario-dependent financial indicators in the Power BI report.

The QA scope covers:

* Base-case investment returns.
* Discounted and undiscounted payback periods.
* Scenario IRR calculations and display behavior.
* Oil-price scenario slicer interactions.
* Consistency between imported comparison data, SQL-view outputs, and Power BI measures.

## 2. Base-Case Investment Returns

### Issue

The Base-Case Investment Returns table displayed payback values that changed with the Oil Price Scenario slicer.

The intended behavior is for this table to provide a stable Base-scenario reference when users select Low, Base, or High elsewhere in the report.

### Source

Imported table: `Scenario Investment Comparison`

Relevant columns:

* `Discounted_Payback_Year`
* `Undiscounted_Payback_Year`

Scenario dimension:

* `Dim_Scenario[Oil_Price_Scenario]`

### Remediation

Two explicit Base-scenario measures were introduced.

```dax
Base-Case Discounted Payback Years =
CALCULATE(
    SELECTEDVALUE(
        'Scenario Investment Comparison'[Discounted_Payback_Year]
    ),
    REMOVEFILTERS('Dim_Scenario'),
    'Dim_Scenario'[Oil_Price_Scenario] = "Base"
)
```

```dax
Base-Case Undiscounted Payback Years =
CALCULATE(
    SELECTEDVALUE(
        'Scenario Investment Comparison'[Undiscounted_Payback_Year]
    ),
    REMOVEFILTERS('Dim_Scenario'),
    'Dim_Scenario'[Oil_Price_Scenario] = "Base"
)
```

The measures explicitly select the Base scenario while preserving the development-concept context.

### Validated reference values

| Development Concept | Base-Case IRR | Discounted Payback (Years) | Undiscounted Payback (Years) |
| ------------------- | ------------: | -------------------------: | ---------------------------: |
| Standalone_FPSO     |        39.62% |                       6.91 |                         6.44 |
| Subsea_Tieback      |        62.44% |                       5.01 |                         4.77 |

### Validation result

**PASS**

The Base-Case Investment Returns table was tested with Low, Base, and High selected in the Oil Price Scenario slicer. The payback values remained stable.

## 3. Scenario IRR

### Issue

The Scenario IRR KPI displayed `N/A` for both development concepts under the Low oil-price scenario.

### Existing measure

```dax
Scenario IRR =
SELECTEDVALUE(
    vw_Scenario_Investment_Comparison[IRR]
)
```

The source `IRR` column was blank for both Low-scenario cases.

The existing display measure converted blank values into the text `N/A`.

### Independent diagnostic findings

Validation script:

`python/validation/validate_scenario_irr.py`

Reported result:

**9 PASSED | 0 FAILED | 9 TOTAL**

The independent diagnostics identified two distinct IRR roots for each Low-scenario development concept.

| Development Concept | Scenario | IRR Roots            | Interpretation        |
| ------------------- | -------- | -------------------- | --------------------- |
| Standalone_FPSO     | Low      | −97.6577%; 28.4919% | Multiple roots        |
| Standalone_FPSO     | Base     | 39.6194%             | Single numerical root |
| Standalone_FPSO     | High     | 49.3888%             | Single numerical root |
| Subsea_Tieback      | Low      | −98.0151%; 40.9733% | Multiple roots        |
| Subsea_Tieback      | Base     | 62.4402%             | Single numerical root |
| Subsea_Tieback      | High     | 81.7045%             | Single numerical root |

The negative roots close to −100% were classified as numerically ill-conditioned. Their NPV residuals were not claimed to be independently verified.

### Remediation

The Scenario IRR display was updated to distinguish the Low-scenario multiple-root condition from a conventional single IRR result.

Expected display:

* Low: `Multiple IRRs`
* Base: calculated IRR percentage
* High: calculated IRR percentage

The underlying financial calculations were not replaced with arbitrary percentages or forced zero values.

### Validation result

**PASS — diagnostic and display behavior**

The independent Python validation passed all nine checks. The dashboard was also confirmed to display `Multiple IRRs` for both development concepts under Low and the calculated percentages under Base and High.

## 4. Slicer and Visual Interaction Requirements

The Oil Price Scenario slicer must continue to control scenario-dependent financial visuals.

The Base-Case Investment Returns table must retain its Base-scenario values independently of the selected oil-price scenario.

The NPV comparison and oil-price sensitivity visuals must retain their intended scenario-comparison behavior.

### Regression status

| Check                                  | Status               |
| -------------------------------------- | -------------------- |
| Base-case payback stability            | PASS                 |
| Low-scenario multiple-IRR display      | PASS                 |
| Base-scenario IRR display              | PASS                 |
| High-scenario IRR display              | PASS                 |
| Independent IRR validation             | PASS                 |
| Full-page slicer and visual regression | Pending final review |

## 5. Data and Calculation Integrity

The following controls were applied:

* Source payback values were inspected in Data view.
* Base-scenario measures were checked against the imported comparison records.
* IRR root analysis was performed independently in Python.
* Multiple-root cases were not silently reduced to a single scalar IRR.
* Existing scenario economics were preserved.

## 6. Finalization Checklist

* [X] Create explicit Base-scenario payback measures.
* [X] Validate Base-case payback values against source data.
* [X] Verify stable payback values across Low, Base, and High.
* [X] Investigate Low-scenario IRR blanks.
* [X] Run independent IRR diagnostics.
* [X] Update the Scenario IRR display behavior.
* [X] Confirm expected Low, Base, and High IRR presentation.
* [ ] Complete final report-wide regression testing.
* [ ] Save the final Power BI report.
* [ ] Commit the updated report and QA documentation to Git.

## 7. Conclusion

The targeted QA work resolved the Base-Case Investment Returns slicer interaction issue and clarified the Low-scenario IRR behavior.

The base-case payback values remain stable across scenario selections. The Low-scenario IRR is explicitly presented as a multiple-root case rather than being represented by an ambiguous single percentage.

Final project closure remains subject to the report-wide regression checks, saving the final `.pbix` file, and committing the approved artifacts to version control.
