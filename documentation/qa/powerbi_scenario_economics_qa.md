# Power BI Scenario Economics — QA Report

## Project Information

**Project:** Offshore Field Development Economics Intelligence
**Component:** Power BI Semantic Model and Executive Dashboard
**QA Scope:** Oil-price scenario analysis, investment returns, and IRR presentation
**Status:** Final dashboard regression completed — 10/10 checks passedcode "documentation\qa\repository_reproducibility_qa.md"

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

The Oil Price Scenario slicer must control scenario-dependent financial visuals. Development Concept selections must update the relevant concept-specific KPIs and comparisons.

The Base-Case Investment Returns table must retain its Base-scenario reference values independently of the selected oil-price scenario.

The NPV comparison, oil-price sensitivity, and annual cash-flow visuals must retain their intended scenario-comparison behavior.

### Regression Results

| Check                                                     | Status |
| --------------------------------------------------------- | ------ |
| Base-case payback stability across Low, Base, and High    | PASS   |
| Low-scenario multiple-IRR display                         | PASS   |
| Base-scenario IRR display                                 | PASS   |
| High-scenario IRR display                                 | PASS   |
| Independent IRR validation                                | PASS   |
| Corrected scenario-comparison visual                      | PASS   |
| Oil-price scenario selection: Low, Base, and High         | PASS   |
| Development concept selection and relevant KPI updates    | PASS   |
| Annual cash-flow scenario and concept interactions        | PASS   |
| Base-case KPI reconciliation against validated references | PASS   |
| Restoration of expected default slicer state              | PASS   |

The additional interaction checks were confirmed during manual Power BI regression testing. Numerical reference values were checked against the project's previously validated base-case outputs.

These checks supplement the original regression results; they should not be interpreted as an independently executed automated test suite.

### Regression Acceptance Criteria

The report is considered to meet the tested interaction requirements when:

* Each oil-price scenario displays the appropriate scenario-dependent results.
* Development concept selections update the relevant KPIs.
* The corrected scenario-comparison visual displays data.
* Annual cash-flow visuals respond to the intended scenario and concept context.
* Base-case reference metrics remain consistent with the validated economics calculations.
* Restoring the default slicer selections returns the report to its expected state.

**Result: PASS — all additional user-confirmed interaction checks passed**

The Base-Case Investment Returns table must retain its Base-scenario values independently of the selected oil-price scenario.

The NPV comparison and oil-price sensitivity visuals must retain their intended scenario-comparison behavior.

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
* [X] Complete final report-wide regression testing.
* [X] Save the final Power BI report.
* [X] Commit the updated report and QA documentation to Git.

## 7. Conclusion

The Power BI scenario economics QA process resolved the Base-Case Investment Returns slicer interaction issue and clarified the presentation of Low-scenario IRR results.

The base-case payback values remain stable across oil-price scenario selections. Low-scenario IRR results are explicitly identified as multiple-root cases rather than being represented by an ambiguous single percentage.

Final dashboard regression testing was completed, with all 10 reported regression checks passing. The final Power BI report was saved, and the approved report and QA documentation were committed to version control.

The scenario economics calculations, slicer interactions, investment metrics, visual consistency, and filter-reset behavior were reviewed as part of the regression process.

The technical QA results support closure of the Power BI scenario economics validation.

**Final QA Status: PASS — 10/10 regression checks passed.**

### Additional Regression Evidence

Subsequent manual regression checks confirmed the corrected scenario-comparison visual, scenario-dependent annual cash flows, development concept selection, base-case reference metrics, and restoration of the expected default report state.

These results supplement the previously documented regression testing. The additional checks were confirmed manually and do not replace the independent Python, SQL, or DAX validation evidence.

**Additional interaction checks: PASS — 8/8 user-confirmed checks.**
