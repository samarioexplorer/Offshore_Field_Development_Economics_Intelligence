from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"

FILES = {
    "economic": DOCS / "economic_assumptions.csv",
    "production": DOCS / "production_profile_assumptions.csv",
    "capex": DOCS / "development_capex_schedule.csv",
    "opex": DOCS / "operating_cost_assumptions.csv",
}

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


def load_csv(key, required_columns):
    path = FILES[key]

    if not path.exists():
        check(False, f"{key}: file exists")
        return None

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception as exc:
        check(False, f"{key}: CSV can be read ({exc})")
        return None

    check(not df.empty, f"{key}: file contains records")

    missing = set(required_columns) - set(df.columns)
    check(not missing, f"{key}: required columns are present")

    if missing:
        print(f"       Missing columns: {sorted(missing)}")
        return None

    return df


def numeric_value(df, record_id, id_column, value_column):
    rows = df.loc[df[id_column] == record_id, value_column]

    if len(rows) != 1:
        raise ValueError(
            f"Expected exactly one {record_id} in {id_column}; found {len(rows)}"
        )

    return float(rows.iloc[0])


def main():
    print("=" * 72)
    print("PROJECT 3 — ASSUMPTION VALIDATION")
    print("Aster Deepwater Field")
    print("=" * 72)

    economic = load_csv(
        "economic",
        [
            "Assumption_ID",
            "Parameter",
            "Development_Concept",
            "Value",
            "Unit",
            "Assumption_Type",
        ],
    )

    production = load_csv(
        "production",
        [
            "Assumption_ID",
            "Development_Concept",
            "Parameter",
            "Value",
            "Unit",
            "Assumption_Type",
        ],
    )

    capex = load_csv(
        "capex",
        [
            "Schedule_ID",
            "Development_Concept",
            "Project_Year",
            "CAPEX_USD",
            "Assumption_Type",
        ],
    )

    opex = load_csv(
        "opex",
        [
            "Cost_ID",
            "Development_Concept",
            "Cost_Component",
            "Value",
            "Unit",
            "Assumption_Type",
        ],
    )

    datasets = {
        "economic": (economic, "Assumption_ID"),
        "production": (production, "Assumption_ID"),
        "capex": (capex, "Schedule_ID"),
        "opex": (opex, "Cost_ID"),
    }

    for name, (df, id_column) in datasets.items():
        if df is None:
            continue

        check(
            df[id_column].notna().all()
            and df[id_column].astype(str).str.strip().ne("").all(),
            f"{name}: identifiers are populated",
        )

        check(
            not df[id_column].duplicated().any(),
            f"{name}: identifiers are unique",
        )

        check(
            df["Assumption_Type"].notna().all()
            and df["Assumption_Type"].astype(str).str.strip().ne("").all(),
            f"{name}: assumption classifications are populated",
        )

        check(
            not df["Assumption_Type"].eq("Pending_Design").any(),
            f"{name}: no Pending_Design placeholders remain",
        )

    if any(df is None for df, _ in datasets.values()):
        print("\nValidation stopped because one or more files could not be loaded.")
        print(f"Failures: {len(errors)}")
        return 1

    # Validate numeric fields.
    for name, df, columns in [
        ("economic", economic, ["Value"]),
        ("production", production, ["Value"]),
        ("capex", capex, ["Project_Year", "CAPEX_USD"]),
        ("opex", opex, ["Value"]),
    ]:
        for column in columns:
            converted = pd.to_numeric(df[column], errors="coerce")

            check(
                converted.notna().all(),
                f"{name}: {column} contains numeric values",
            )

            check(
                converted.map(lambda value: pd.notna(value) and abs(value) != float("inf")).all(),
                f"{name}: {column} contains finite values",
            )

            df[column] = converted

    # Stop semantic validation if numeric data is malformed.
    if errors:
        print("\nNumeric or structural errors must be corrected before reconciliation.")
        print(f"Checks passed: {passed}")
        print(f"Checks failed: {len(errors)}")
        return 1

    # Validate development concepts.
    concepts = {"Subsea_Tieback", "Standalone_FPSO", "Shared"}

    for name, df in [
        ("economic", economic),
        ("production", production),
        ("capex", capex),
        ("opex", opex),
    ]:
        check(
            set(df["Development_Concept"]).issubset(concepts),
            f"{name}: development concepts use approved labels",
        )

    # Validate core economic assumptions.
    core_expected = {
        "A001": 3,
        "A002": 4,
        "A003": 60000,
        "A004": 100000,
        "A005": 75,
        "A006": 0.10,
        "A007": 25,
        "A008": 365,
    }

    for assumption_id, expected in core_expected.items():
        try:
            actual = numeric_value(
                economic, assumption_id, "Assumption_ID", "Value"
            )
            check(
                abs(actual - expected) < 1e-9,
                f"economic: {assumption_id} matches the proposed base case",
            )
        except ValueError as exc:
            check(False, f"economic: {exc}")

    # Cross-file reconciliation: first oil, capacity, and annual days.
    profile_mappings = {
        "P001": "A001",
        "P002": "A002",
        "P003": "A003",
        "P004": "A004",
        "P011": "A008",
    }

    for profile_id, economic_id in profile_mappings.items():
        try:
            profile_value = numeric_value(
                production, profile_id, "Assumption_ID", "Value"
            )
            economic_value = numeric_value(
                economic, economic_id, "Assumption_ID", "Value"
            )

            check(
                abs(profile_value - economic_value) < 1e-9,
                f"cross-file: {profile_id} reconciles with {economic_id}",
            )
        except ValueError as exc:
            check(False, f"cross-file reconciliation: {exc}")

    # Validate production-profile parameters.
    profile_expected = {
        "P005": 0.60,
        "P006": 0.85,
        "P007": 1.00,
        "P008": 5,
        "P009": 0.08,
        "P010": 0.90,
    }

    for assumption_id, expected in profile_expected.items():
        try:
            actual = numeric_value(
                production, assumption_id, "Assumption_ID", "Value"
            )
            check(
                abs(actual - expected) < 1e-9,
                f"production: {assumption_id} matches the proposed profile",
            )
        except ValueError as exc:
            check(False, f"production: {exc}")

    try:
        initial_ramp = numeric_value(
            production, "P005", "Assumption_ID", "Value"
        )
        second_ramp = numeric_value(
            production, "P006", "Assumption_ID", "Value"
        )
        plateau = numeric_value(
            production, "P007", "Assumption_ID", "Value"
        )
        decline = numeric_value(
            production, "P009", "Assumption_ID", "Value"
        )
        uptime = numeric_value(
            production, "P010", "Assumption_ID", "Value"
        )

        check(
            0 < initial_ramp <= second_ramp <= plateau <= 1,
            "production: ramp and plateau factors are ordered and bounded",
        )

        check(
            0 <= decline < 1,
            "production: annual decline rate is between 0 and 100%",
        )

        check(
            0 < uptime <= 1,
            "production: uptime factor is greater than zero and at most 100%",
        )
    except ValueError as exc:
        check(False, f"production parameter validation: {exc}")

    # Validate CAPEX schedules and totals.
    check(
        capex["Project_Year"].between(1, 25).all()
        and (capex["Project_Year"] % 1 == 0).all(),
        "CAPEX: project years are integers within the evaluation horizon",
    )

    check(
        (capex["CAPEX_USD"] >= 0).all(),
        "CAPEX: no negative expenditure entries",
    )

    check(
        not capex.duplicated(["Development_Concept", "Project_Year"]).any(),
        "CAPEX: at most one schedule row per concept and project year",
    )

    capex_totals = capex.groupby("Development_Concept")["CAPEX_USD"].sum()

    for concept, expected in {
        "Subsea_Tieback": 1_300_000_000,
        "Standalone_FPSO": 4_000_000_000,
    }.items():
        actual = float(capex_totals.get(concept, float("nan")))

        check(
            abs(actual - expected) < 0.01,
            f"CAPEX: {concept} total reconciles to ${expected:,.0f}",
        )

    # Reconcile operating costs to the master assumptions register.
    cost_mappings = {
        "A009": ("O001", "Fixed_OPEX"),
        "A010": ("O002", "Variable_OPEX"),
        "A011": ("O003", "Host_Tariff"),
        "A012": ("O005", "Fixed_OPEX"),
        "A013": ("O006", "Variable_OPEX"),
        "A014": ("O004", "Abandonment"),
        "A015": ("O008", "Abandonment"),
    }

    for master_id, (cost_id, expected_component) in cost_mappings.items():
        try:
            master_value = numeric_value(
                economic, master_id, "Assumption_ID", "Value"
            )
            schedule_value = numeric_value(
                opex, cost_id, "Cost_ID", "Value"
            )

            component = opex.loc[
                opex["Cost_ID"] == cost_id, "Cost_Component"
            ].iloc[0]

            check(
                abs(master_value - schedule_value) < 1e-9,
                f"OPEX: {master_id} reconciles with {cost_id}",
            )

            check(
                component == expected_component,
                f"OPEX: {cost_id} has the expected cost component",
            )
        except (ValueError, IndexError) as exc:
            check(False, f"OPEX reconciliation: {exc}")

    try:
        fpsO_tariff = numeric_value(
            opex, "O007", "Cost_ID", "Value"
        )
        check(
            abs(fpsO_tariff) < 1e-9,
            "OPEX: standalone FPSO host tariff is zero as specified",
        )
    except ValueError as exc:
        check(False, f"OPEX tariff validation: {exc}")

    check(
        (opex["Value"] >= 0).all(),
        "OPEX: all cost rates and amounts are non-negative",
    )

    # Final report.
    print("\n" + "=" * 72)
    print("VALIDATION SUMMARY")
    print("=" * 72)
    print(f"Checks passed: {passed}")
    print(f"Checks failed: {len(errors)}")

    if errors:
        print("\nIssues requiring attention:")
        for error in errors:
            print(f"- {error}")

        print("\nRESULT: FAIL — do not generate economic results yet.")
        return 1

    print("\nRESULT: PASS — assumption files passed the current validation suite.")
    print("Note: This validates assumptions and schedules, not economic outputs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
