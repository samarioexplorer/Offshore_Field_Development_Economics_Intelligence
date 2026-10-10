from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"
OUTPUT_DIR = ROOT / "data" / "processed"

PROFILE_FILE = DOCS / "production_profile_assumptions.csv"
OUTPUT_FILE = OUTPUT_DIR / "annual_production_profiles.csv"

EVALUATION_HORIZON = 25


def load_profile_assumptions():
    df = pd.read_csv(PROFILE_FILE, encoding="utf-8-sig")

    required = {
        "Assumption_ID",
        "Development_Concept",
        "Parameter",
        "Value",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing production-profile columns: {sorted(missing)}"
        )

    if df["Assumption_ID"].duplicated().any():
        raise ValueError("Duplicate production-profile assumption IDs.")

    df["Value"] = pd.to_numeric(df["Value"], errors="raise")

    return df


def get_value(df, assumption_id):
    rows = df.loc[
        df["Assumption_ID"] == assumption_id,
        "Value",
    ]

    if len(rows) != 1:
        raise ValueError(
            f"Expected exactly one record for {assumption_id}; "
            f"found {len(rows)}."
        )

    return float(rows.iloc[0])


def production_factor(producing_year, initial_ramp,
                      second_ramp, plateau_factor,
                      plateau_duration, decline_rate):
    if producing_year == 1:
        return initial_ramp

    if producing_year == 2:
        return second_ramp

    # The five-year plateau begins in production year 3.
    plateau_start = 3
    plateau_end = plateau_start + plateau_duration - 1

    if plateau_start <= producing_year <= plateau_end:
        return plateau_factor

    if producing_year > plateau_end:
        decline_years = producing_year - plateau_end

        return plateau_factor * (
            (1 - decline_rate) ** decline_years
        )

    raise ValueError(
        f"Unexpected producing year: {producing_year}"
    )


def generate_profiles():
    assumptions = load_profile_assumptions()

    first_oil_tieback = int(get_value(assumptions, "P001"))
    first_oil_fpso = int(get_value(assumptions, "P002"))

    capacity_tieback = get_value(assumptions, "P003")
    capacity_fpso = get_value(assumptions, "P004")

    initial_ramp = get_value(assumptions, "P005")
    second_ramp = get_value(assumptions, "P006")
    plateau_factor = get_value(assumptions, "P007")
    plateau_duration = int(get_value(assumptions, "P008"))
    decline_rate = get_value(assumptions, "P009")
    uptime = get_value(assumptions, "P010")
    annual_days = int(get_value(assumptions, "P011"))

    concepts = [
        {
            "concept": "Subsea_Tieback",
            "first_oil": first_oil_tieback,
            "capacity": capacity_tieback,
        },
        {
            "concept": "Standalone_FPSO",
            "first_oil": first_oil_fpso,
            "capacity": capacity_fpso,
        },
    ]

    records = []

    for concept in concepts:
        for project_year in range(1, EVALUATION_HORIZON + 1):
            producing_year = (
                project_year - concept["first_oil"] + 1
            )

            if producing_year <= 0:
                factor = 0.0
                oil_rate = 0.0
                annual_oil = 0.0
            else:
                factor = production_factor(
                    producing_year,
                    initial_ramp,
                    second_ramp,
                    plateau_factor,
                    plateau_duration,
                    decline_rate,
                )

                oil_rate = (
                    concept["capacity"]
                    * factor
                    * uptime
                )

                annual_oil = oil_rate * annual_days

            records.append(
                {
                    "Development_Concept": concept["concept"],
                    "Project_Year": project_year,
                    "Producing_Year": max(producing_year, 0),
                    "First_Oil_Year": concept["first_oil"],
                    "Maximum_Capacity_bbl_per_day": concept["capacity"],
                    "Production_Profile_Factor": factor,
                    "Uptime_Factor": uptime,
                    "Effective_Oil_Rate_bbl_per_day": oil_rate,
                    "Annual_Production_Days": annual_days,
                    "Annual_Oil_Production_bbl": annual_oil,
                    "Assumption_Status": "Proposed_Illustrative",
                }
            )

    result = pd.DataFrame(records)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(OUTPUT_FILE, index=False)

    print("=" * 72)
    print("ANNUAL PRODUCTION PROFILE GENERATION")
    print("=" * 72)
    print(f"Output: {OUTPUT_FILE}")
    print(f"Records generated: {len(result):,}")
    print(f"Development concepts: {result['Development_Concept'].nunique()}")
    print(
        f"Evaluation years per concept: "
        f"{result['Project_Year'].nunique()}"
    )

    print("\nProduction summary:")

    summary = (
        result.groupby("Development_Concept")
        .agg(
            Total_Production_bbl=(
                "Annual_Oil_Production_bbl",
                "sum",
            ),
            First_Oil_Year=("First_Oil_Year", "first"),
            Maximum_Capacity_bbl_per_day=(
                "Maximum_Capacity_bbl_per_day",
                "first",
            ),
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    print("\nFirst production years:")
    print(
        result.loc[
            result["Producing_Year"].between(1, 7),
            [
                "Development_Concept",
                "Project_Year",
                "Producing_Year",
                "Production_Profile_Factor",
                "Effective_Oil_Rate_bbl_per_day",
                "Annual_Oil_Production_bbl",
            ],
        ].to_string(index=False)
    )


if __name__ == "__main__":
    generate_profiles()
