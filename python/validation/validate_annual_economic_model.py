from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "documentation"

MODEL_FILE = PROCESSED / "annual_economic_model.csv"
PRODUCTION_FILE = PROCESSED / "annual_production_profiles.csv"
ECONOMIC_FILE = DOCS / "economic_assumptions.csv"
CAPEX_FILE = DOCS / "development_capex_schedule.csv"
OPEX_FILE = DOCS / "operating_cost_assumptions.csv"

errors = []
passed = 0


def check(condition, message):
    global passed

    if condition:
        passed += 1
        print(f"[PASS] {message}")
    else:
        errors.append(message)
        print(f"[FAIL] {message}")


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return pd.read_csv(path, encoding="utf-8-sig")


def get_assumption(df, assumption_id):
    rows = df.loc[
        df["Assumption_ID"] == assumption_id,
        "Value",
    ]

    if len(rows) != 1:
        raise ValueError(
            f"Expected one assumption {assumption_id}; found {len(rows)}."
        )

    return float(rows.iloc[0])


def get_cost(opex, concept, component):
    rows = opex.loc[
        (opex["Development_Concept"] == concept)
        & (opex["Cost_Component"] == component),
        "Value",
    ]

    if len(rows) != 1:
        raise ValueError(
            f"Expected one {component} record for {concept}; "
            f"found {len(rows)}."
        )

    return float(rows.iloc[0])


def main():
    print("=" * 72)
    print("PROJECT 3 — ANNUAL ECONOMIC MODEL QA")
    print("=" * 72)

    model = read_csv(MODEL_FILE)
    production = read_csv(PRODUCTION_FILE)
    economic = read_csv(ECONOMIC_FILE)
    capex = read_csv(CAPEX_FILE)
    opex = read_csv(OPEX_FILE)

    required_columns = {
        "Development_Concept",
        "Project_Year",
        "Annual_Oil_Production_bbl",
        "Oil_Price_USD_per_bbl",
        "Revenue_USD",
        "CAPEX_USD",
        "Fixed_OPEX_USD",
        "Variable_OPEX_USD",
        "Host_Tariff_USD",
        "Total_OPEX_USD",
        "Abandonment_USD",
        "Net_Project_Cash_Flow_USD",
        "Cumulative_Net_Cash_Flow_USD",
    }

    check(
        required_columns.issubset(model.columns),
        "All required economic model columns are present",
    )

    if not required_columns.issubset(model.columns):
        print("\nQA stopped: required columns are missing.")
        return 1

    concepts = {"Subsea_Tieback", "Standalone_FPSO"}

    check(
        set(model["Development_Concept"]) == concepts,
        "Exactly the two expected development concepts are present",
    )

    check(
        len(model) == 50,
        "Exactly 50 annual economic records are present",
    )

    check(
        not model.duplicated(
            ["Development_Concept", "Project_Year"]
        ).any(),
        "No duplicate concept-year economic records",
    )

    check(
        model.groupby("Development_Concept").size().eq(25).all(),
        "Each development concept has 25 annual records",
    )

    numeric_columns = [
        "Project_Year",
        "Annual_Oil_Production_bbl",
        "Oil_Price_USD_per_bbl",
        "Revenue_USD",
        "CAPEX_USD",
        "Fixed_OPEX_USD",
        "Variable_OPEX_USD",
        "Host_Tariff_USD",
        "Total_OPEX_USD",
        "Abandonment_USD",
        "Net_Project_Cash_Flow_USD",
        "Cumulative_Net_Cash_Flow_USD",
    ]

    for column in numeric_columns:
        model[column] = pd.to_numeric(
            model[column],
            errors="coerce",
        )

        check(
            model[column].notna().all()
            and np.isfinite(model[column]).all(),
            f"{column}: values are numeric and finite",
        )

    if errors:
        print("\nStructural or numeric errors must be resolved first.")
        print(f"Checks passed: {passed}")
        print(f"Checks failed: {len(errors)}")
        return 1

    model = model.sort_values(
        ["Development_Concept", "Project_Year"]
    ).reset_index(drop=True)

    production = production.sort_values(
        ["Development_Concept", "Project_Year"]
    ).reset_index(drop=True)

    # Validate the base oil price and evaluation horizon.
    base_price = get_assumption(economic, "A005")
    horizon = int(get_assumption(economic, "A007"))

    check(
        np.allclose(model["Oil_Price_USD_per_bbl"], base_price),
        "All annual records use the documented base oil price",
    )

    check(
        model["Project_Year"].between(1, horizon).all(),
        "Economic records remain within the evaluation horizon",
    )

    # Independently reconcile annual production to its source.
    source_production = production[
        [
            "Development_Concept",
            "Project_Year",
            "Annual_Oil_Production_bbl",
        ]
    ].rename(
        columns={
            "Annual_Oil_Production_bbl": "Source_Production_bbl"
        }
    )

    reconciled = model.merge(
        source_production,
        on=["Development_Concept", "Project_Year"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    check(
        reconciled["_merge"].eq("both").all(),
        "Every economic record matches a production source record",
    )

    check(
        np.allclose(
            reconciled["Annual_Oil_Production_bbl"],
            reconciled["Source_Production_bbl"],
            rtol=0,
            atol=1e-6,
        ),
        "Annual production reconciles to the production source",
    )

    # Independently reconstruct the CAPEX schedule.
    for concept in sorted(concepts):
        annual = model.loc[
            model["Development_Concept"] == concept
        ].sort_values("Project_Year")

        expected_capex = (
            capex.loc[
                capex["Development_Concept"] == concept
            ]
            .set_index("Project_Year")["CAPEX_USD"]
        )

        expected_capex = (
            expected_capex.reindex(range(1, horizon + 1))
            .fillna(0.0)
        )

        check(
            np.allclose(
                annual["CAPEX_USD"].to_numpy(),
                expected_capex.to_numpy(),
                rtol=0,
                atol=0.01,
            ),
            f"{concept}: annual CAPEX reconciles to the schedule",
        )

    check(
        (model["CAPEX_USD"] >= 0).all(),
        "CAPEX values are non-negative",
    )

    # Recalculate each cost component independently.
    expected_fixed = []
    expected_variable = []
    expected_tariff = []
    expected_abandonment = []

    for _, row in model.iterrows():
        concept = row["Development_Concept"]
        production_bbl = row["Annual_Oil_Production_bbl"]
        project_year = int(row["Project_Year"])

        fixed_rate = get_cost(opex, concept, "Fixed_OPEX")
        variable_rate = get_cost(opex, concept, "Variable_OPEX")
        tariff_rate = get_cost(opex, concept, "Host_Tariff")
        abandonment_rate = get_cost(opex, concept, "Abandonment")

        expected_fixed.append(
            fixed_rate if production_bbl > 0 else 0.0
        )

        expected_variable.append(
            production_bbl * variable_rate
        )

        expected_tariff.append(
            production_bbl * tariff_rate
        )

        expected_abandonment.append(
            abandonment_rate if project_year == horizon else 0.0
        )

    check(
        np.allclose(
            model["Fixed_OPEX_USD"],
            expected_fixed,
            rtol=0,
            atol=0.01,
        ),
        "Fixed OPEX reconciles to producing-year rules",
    )

    check(
        np.allclose(
            model["Variable_OPEX_USD"],
            expected_variable,
            rtol=0,
            atol=0.01,
        ),
        "Variable OPEX reconciles to production and cost rates",
    )

    check(
        np.allclose(
            model["Host_Tariff_USD"],
            expected_tariff,
            rtol=0,
            atol=0.01,
        ),
        "Host tariff reconciles to production and tariff rates",
    )

    check(
        np.allclose(
            model["Abandonment_USD"],
            expected_abandonment,
            rtol=0,
            atol=0.01,
        ),
        "Abandonment expenditure occurs only in Project Year 25",
    )

    expected_total_opex = (
        model["Fixed_OPEX_USD"]
        + model["Variable_OPEX_USD"]
        + model["Host_Tariff_USD"]
    )

    check(
        np.allclose(
            model["Total_OPEX_USD"],
            expected_total_opex,
            rtol=0,
            atol=0.01,
        ),
        "Total OPEX reconciles to its three components",
    )

    # Revenue reconciliation.
    expected_revenue = (
        model["Annual_Oil_Production_bbl"]
        * model["Oil_Price_USD_per_bbl"]
    )

    check(
        np.allclose(
            model["Revenue_USD"],
            expected_revenue,
            rtol=0,
            atol=0.01,
        ),
        "Revenue reconciles to annual production and oil price",
    )

    # Net cash-flow reconciliation.
    expected_cash_flow = (
        model["Revenue_USD"]
        - model["CAPEX_USD"]
        - model["Total_OPEX_USD"]
        - model["Abandonment_USD"]
    )

    check(
        np.allclose(
            model["Net_Project_Cash_Flow_USD"],
            expected_cash_flow,
            rtol=0,
            atol=0.01,
        ),
        "Net project cash flow reconciles independently",
    )

    # Cumulative cash-flow reconciliation.
    expected_cumulative = (
        model.groupby("Development_Concept")[
            "Net_Project_Cash_Flow_USD"
        ].cumsum()
    )

    check(
        np.allclose(
            model["Cumulative_Net_Cash_Flow_USD"],
            expected_cumulative,
            rtol=0,
            atol=0.01,
        ),
        "Cumulative cash flow reconciles independently",
    )

    # Ensure fixed OPEX is zero before first oil.
    before_first_oil = model["Annual_Oil_Production_bbl"] == 0

    check(
        (
            model.loc[before_first_oil, "Fixed_OPEX_USD"] == 0
        ).all(),
        "Fixed OPEX is zero in years without production",
    )

    check(
        (
            model.loc[before_first_oil, "Variable_OPEX_USD"] == 0
        ).all()
        and (
            model.loc[before_first_oil, "Host_Tariff_USD"] == 0
        ).all(),
        "Variable OPEX and host tariff are zero before production",
    )

    # Check summary totals against independently recomputed values.
    print("\nIndependently reconciled economic summary:")

    summary = (
        model.groupby("Development_Concept")
        .agg(
            Production_bbl=("Annual_Oil_Production_bbl", "sum"),
            Revenue_USD=("Revenue_USD", "sum"),
            CAPEX_USD=("CAPEX_USD", "sum"),
            OPEX_USD=("Total_OPEX_USD", "sum"),
            Abandonment_USD=("Abandonment_USD", "sum"),
            Net_Cash_Flow_USD=("Net_Project_Cash_Flow_USD", "sum"),
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    print("\n" + "=" * 72)
    print("ECONOMIC MODEL QA SUMMARY")
    print("=" * 72)
    print(f"Checks passed: {passed}")
    print(f"Checks failed: {len(errors)}")

    if errors:
        print("\nIssues requiring attention:")
        for error in errors:
            print(f"- {error}")

        print("\nRESULT: FAIL — do not calculate investment indicators yet.")
        return 1

    print("\nRESULT: PASS — annual economic cash flows passed QA.")
    print("NPV, IRR, payback, and breakeven have not yet been validated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
