# Finding 2 — Database Publication and Repository Reproducibility

**Disposition:** CLOSED — TECHNICAL PORTION
**Result:** PASS

## Objective

Verify that the Offshore Field Development Economics Intelligence analytical outputs and SQLite database can be regenerated using the repository's source assumptions, Python scripts, and SQL definitions without requiring generated CSV files or the database to be committed to Git.

## Verification performed

The end-to-end pipeline was executed using:

`py python/run_pipeline.py`

The pipeline completed all 14 steps successfully in 26.29 seconds.

The execution validated source assumptions, generated production profiles, built the annual economic model, calculated investment metrics, generated oil-price scenarios, diagnosed scenario IRR roots, built the SQLite database, created six analytical SQL views, and performed independent reconciliation.

## Evidence

* Assumption validation: 81 checks passed.
* Production profile validation: 23 checks passed.
* Annual economic model validation: 34 checks passed.
* Investment metrics validation: 17 checks passed.
* Oil-price scenario validation: 16 checks passed.
* Scenario IRR diagnostics: 9 checks passed.
* SQLite integrity check: `ok`.
* Analytical records loaded: 408/408.
* SQL analytical view validation: 15/15 checks passed.
* Independent SQL reconciliation: 10/10 checks passed.
* Pipeline execution: 14/14 steps passed.

The four primary source assumption files are tracked in Git. Generated CSV outputs and the SQLite database remain excluded under the repository's existing ignore rules. The Power BI file's existing local modification was preserved during pipeline execution.

## Clean-Checkout Reproducibility Verification

### Objective

Verify that the committed repository can regenerate its analytical outputs and SQLite database from a fresh Git checkout using an isolated Python environment.

### Test environment

* Operating system: Windows
* Python version: 3.14.6
* Repository source: Fresh clone of the GitHub `main` branch
* Python environment: New repository-local virtual environment
* Dependencies: Installed from `requirements.txt`
* Pipeline command: `python python/run_pipeline.py`

### Verification procedure

1. Cloned the committed GitHub repository into a separate temporary directory.
2. Confirmed that the fresh checkout had no uncommitted changes.
3. Created a new Python virtual environment.
4. Installed the dependencies specified in `requirements.txt`.
5. Executed the pipeline without using the original working repository's generated outputs or SQLite database.
6. Reviewed the pipeline execution and validation results.

### Results

The clean-checkout pipeline completed all 14 steps successfully in 21.33 seconds.

| Validation                       |             Result |
| -------------------------------- | -----------------: |
| Assumption validation            |          81 passed |
| Production profile validation    |          23 passed |
| Annual economic model validation |          34 passed |
| Investment metrics validation    |          17 passed |
| Oil-price scenario validation    |          16 passed |
| Scenario IRR diagnostics         |           9 passed |
| SQLite integrity                 |             `ok` |
| Analytical records loaded        |            408/408 |
| SQL analytical view validation   |       15/15 passed |
| Independent SQL reconciliation   |       10/10 passed |
| End-to-end pipeline              | 14/14 steps passed |

The pipeline regenerated the synthetic production profiles, annual economic model, investment metrics, oil-price scenario outputs, discounted cash-flow schedules, SQLite database, and six analytical SQL views.

The independently calculated base-case NPV, IRR, payback, and breakeven metrics agreed with the project's established reference results.

### Conclusion

**Clean-checkout reproducibility: PASS.**

The repository successfully regenerated its analytical outputs and SQLite database from a fresh checkout using a newly created Python virtual environment.

This verification establishes reproducibility for the tested Python, CSV, SQLite, and SQL pipeline. It does not independently verify a clean rebuild of the Power BI semantic model or report.

The economic outputs remain synthetic and illustrative, not actual asset forecasts or investment recommendations.

The technical portion of Finding 2 is therefore closed.

Initial verification was performed in the existing working environment. Subsequent clean-checkout testing confirmed that the committed repository can regenerate its analytical outputs in an isolated Python environment.

## Outstanding administrative action

## Administrative Closure

The verification record has been added to the repository.
The approved documentation and Power BI deliverable were committed
and pushed to the main branch.

Commit: `f07496e`

The local working tree was subsequently verified as clean.

## Final Disposition

Technical verification: PASS.
Documentation and publication: COMPLETE.
Finding 2: CLOSED.

**Final technical disposition: PASS — CLOSED. **

The successful pipeline execution and independent SQL validation support the technical closure. The verification was performed in the existing working environment; a clean-checkout rebuild was not performed.
