
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

## Conclusion

The technical verification passed. The pipeline successfully regenerated the analytical outputs and SQLite database, and independent validation confirmed database integrity, expected row counts, analytical-view consistency, and cross-layer reconciliation.

The technical portion of Finding 2 is therefore closed.

The closure is based on a successful rebuild in the current working environment; a clean-checkout reproducibility test has not been claimed.

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
