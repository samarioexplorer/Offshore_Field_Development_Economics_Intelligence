from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "annual_production_profiles.csv"
)

ASSUMPTION_FILE = (
    ROOT
    / "documentation"
    / "production_profile_assumptions.csv"
)

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


def load_assumptions():
    df = pd.read_csv(ASSUMPTION_FILE, encoding="utf-8-sig")

    if df["Assumption_ID"].duplicated().any():
        raise ValueError("Duplicate production assumption IDs.")

    df["Value"] = pd.to_numeric(df["Value"], errors="raise")

    return dict(zip(df["Assumption_ID"], df["Value"]))


def expected_factor(
    producing_year,
    initial_ramp,
    second_ramp,
    plateau_factor,
    plateau_duration,
    decline_rate,
):
    if producing_year <= 0:
        return 0.0

    if producing_year == 1:
        return initial_ramp

    if producing_year == 2:
        return second_ramp

    plateau_start = 3
    plateau_end = plateau_start + plateau_duration - 1

    if producing_year <= plateau_end:
        return plateau_factor

    decline_years = producing_year - plateau_end

    return plateau_factor * (1 - decline_rate) ** decline_years


def main():
    global passed

    print("=" * 72)
    print("PROJECT 3 — PRODUCTION PROFILE VALIDATION")
    print("=" * 72)

    if not INPUT_FILE.exists():
        print(f"[FAIL] Production output not found: {INPUT_FILE}")
        return 1

    if not ASSUMPTION_FILE.exists():
        print(f"[FAIL] Assumption file not found: {ASSUMPTION_FILE}")
        return 1

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    assumptions = load_assumptions()

    required_columns = {
        "Development_Concept",
        "Project_Year",
        "Producing_Year",
        "First_Oil_Year",
        "Maximum_Capacity_bbl_per_day",
        "Production_Profile_Factor",
        "Uptime_Factor",
        "Effective_Oil_Rate_bbl_per_day",
        "Annual_Production_Days",
        "Annual_Oil_Production_bbl",
    }

    check(
        required_columns.issubset(df.columns),
        "All required production columns are present",
    )

    if not required_columns.issubset(df.columns):
        print("\nCannot continue: required columns are missing.")
        return 1

    concepts = {"Subsea_Tieback", "Standalone_FPSO"}

    check(
        set(df["Development_Concept"]) == concepts,
        "Exactly the two expected development concepts are present",
    )

    check(
        len(df) == 50,
        "Exactly 50 annual records are generated",
    )

    check(
        not df.duplicated(
            ["Development_Concept", "Project_Year"]
        ).any(),
        "No duplicate concept-year records",
    )

    check(
        df["Project_Year"].between(1, 25).all(),
        "All project years fall within the 25-year horizon",
    )

    check(
        df.groupby("Development_Concept").size().eq(25).all(),
        "Each concept has exactly 25 annual records",
    )

    check(
        df.groupby("Development_Concept")["Project_Year"]
        .apply(lambda s: sorted(s.tolist()) == list(range(1, 26)))
        .all(),
        "Each concept has a complete, uninterrupted project-year sequence",
    )

    # Load expected values from the documented assumptions.
    first_oil = {
        "Subsea_Tieback": int(assumptions["P001"]),
        "Standalone_FPSO": int(assumptions["P002"]),
    }

    capacity = {
        "Subsea_Tieback": assumptions["P003"],
        "Standalone_FPSO": assumptions["P004"],
    }

    initial_ramp = assumptions["P005"]
    second_ramp = assumptions["P006"]
    plateau_factor = assumptions["P007"]
    plateau_duration = int(assumptions["P008"])
    decline_rate = assumptions["P009"]
    uptime = assumptions["P010"]
    annual_days = int(assumptions["P011"])

    expected_horizon = 25

    check(
        (df["Annual_Production_Days"] == annual_days).all(),
        "Annual production days match the assumptions",
    )

    check(
        np.allclose(df["Uptime_Factor"], uptime),
        "Uptime factor matches the assumptions",
    )

    check(
        np.allclose(
            df["Maximum_Capacity_bbl_per_day"],
            df["Development_Concept"].map(capacity),
        ),
        "Maximum capacity matches the appropriate development concept",
    )

    check(
        (
            df["First_Oil_Year"]
            == df["Development_Concept"].map(first_oil)
        ).all(),
        "First-oil year matches the assumptions",
    )

    # Independently calculate producing year and profile factor.
    expected_producing_year = (
        df["Project_Year"]
        - df["Development_Concept"].map(first_oil)
        + 1
    ).clip(lower=0)

    check(
        (df["Producing_Year"] == expected_producing_year).all(),
        "Producing-year sequence is correct",
    )

    expected_profile = []

    for _, row in df.iterrows():
        producing_year = int(row["Producing_Year"])

        expected_profile.append(
            expected_factor(
                producing_year,
                initial_ramp,
                second_ramp,
                plateau_factor,
                plateau_duration,
                decline_rate,
            )
        )

    expected_profile = np.array(expected_profile)

    check(
        np.allclose(
            df["Production_Profile_Factor"],
            expected_profile,
            rtol=0,
            atol=1e-10,
        ),
        "Ramp, plateau, and decline factors match independent calculations",
    )

    # Recalculate rate and annual volume independently.
    expected_rate = (
        df["Maximum_Capacity_bbl_per_day"]
        * expected_profile
        * uptime
    )

    expected_volume = expected_rate * annual_days

    check(
        np.allclose(
            df["Effective_Oil_Rate_bbl_per_day"],
            expected_rate,
            rtol=0,
            atol=1e-8,
        ),
        "Effective production rates reconcile independently",
    )

    check(
        np.allclose(
            df["Annual_Oil_Production_bbl"],
            expected_volume,
            rtol=0,
            atol=1e-6,
        ),
        "Annual oil volumes reconcile independently",
    )

    check(
        (df["Annual_Oil_Production_bbl"] >= 0).all(),
        "No negative annual production volumes",
    )

    check(
        (
            df["Effective_Oil_Rate_bbl_per_day"]
            <= df["Maximum_Capacity_bbl_per_day"] * uptime + 1e-8
        ).all(),
        "Effective production rates never exceed capacity after uptime",
    )

    check(
        (
            df.loc[
                df["Project_Year"] < df["First_Oil_Year"],
                "Annual_Oil_Production_bbl",
            ] == 0
        ).all(),
        "Production is zero before first oil",
    )

    check(
        (
            df.loc[
                df["Project_Year"] < df["First_Oil_Year"],
                "Production_Profile_Factor",
            ] == 0
        ).all(),
        "Production profile factor is zero before first oil",
    )

    # Verify the plateau contains exactly the specified number of years.
    plateau_start = 3
    plateau_end = plateau_start + plateau_duration - 1

    plateau_rows = df.loc[
        df["Producing_Year"].between(plateau_start, plateau_end)
    ]

    check(
        len(plateau_rows) == 2 * plateau_duration,
        "Each concept has the required number of plateau years",
    )

    check(
        np.allclose(
            plateau_rows["Production_Profile_Factor"],
            plateau_factor,
        ),
        "All plateau years use the full plateau factor",
    )

    # Verify the first decline year.
    first_decline_year = plateau_end + 1

    decline_rows = df.loc[
        df["Producing_Year"] == first_decline_year
    ]

    check(
        len(decline_rows) == 2,
        "Both concepts have a first post-plateau decline year",
    )

    check(
        np.allclose(
            decline_rows["Production_Profile_Factor"],
            plateau_factor * (1 - decline_rate),
        ),
        "First post-plateau year applies the specified decline rate",
    )

    # Verify totals independently against the expected profile.
    print("\nProduction totals by concept:")

    summary = (
        df.groupby("Development_Concept")
        .agg(
            Record_Count=("Project_Year", "count"),
            First_Oil_Year=("First_Oil_Year", "first"),
            Total_Production_bbl=("Annual_Oil_Production_bbl", "sum"),
            Peak_Effective_Rate_bbl_per_day=(
                "Effective_Oil_Rate_bbl_per_day",
                "max",
            ),
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    print("\n" + "=" * 72)
    print("PRODUCTION QA SUMMARY")
    print("=" * 72)
    print(f"Checks passed: {passed}")
    print(f"Checks failed: {len(errors)}")

    if errors:
        print("\nIssues requiring attention:")
        for error in errors:
            print(f"- {error}")

        print("\nRESULT: FAIL — do not proceed to economic calculations.")
        return 1

    print("\nRESULT: PASS — production profiles passed independent QA.")
    print("Economic outputs have not yet been validated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
