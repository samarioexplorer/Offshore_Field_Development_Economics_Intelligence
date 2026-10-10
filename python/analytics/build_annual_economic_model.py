from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DOCS = ROOT / "documentation"
PROCESSED = ROOT / "data" / "processed"

PRODUCTION_FILE = PROCESSED / "annual_production_profiles.csv"
ECONOMIC_FILE = DOCS / "economic_assumptions.csv"
CAPEX_FILE = DOCS / "development_capex_schedule.csv"
OPEX_FILE = DOCS / "operating_cost_assumptions.csv"

OUTPUT_FILE = PROCESSED / "annual_economic_model.csv"


def load_csv(path):
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
            f"Expected one record for {assumption_id}; found {len(rows)}."
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
    print("PROJECT 3 — ANNUAL ECONOMIC MODEL")
    print("=" * 72)

    production = load_csv(PRODUCTION_FILE)
    economic = load_csv(ECONOMIC_FILE)
    capex = load_csv(CAPEX_FILE)
    opex = load_csv(OPEX_FILE)

    oil_price = get_assumption(economic, "A005")
    horizon = int(get_assumption(economic, "A007"))

    concepts = ["Subsea_Tieback", "Standalone_FPSO"]

    production["Project_Year"] = pd.to_numeric(
        production["Project_Year"], errors="raise"
    )

    capex["Project_Year"] = pd.to_numeric(
        capex["Project_Year"], errors="raise"
    )

    production["Annual_Oil_Production_bbl"] = pd.to_numeric(
        production["Annual_Oil_Production_bbl"], errors="raise"
    )

    capex["CAPEX_USD"] = pd.to_numeric(
        capex["CAPEX_USD"], errors="raise"
    )

    production_key = ["Development_Concept", "Project_Year"]

    if production.duplicated(production_key).any():
        raise ValueError("Duplicate production concept-year records.")

    if capex.duplicated(production_key).any():
        raise ValueError("Duplicate CAPEX concept-year records.")

    records = []

    for concept in concepts:
        concept_production = production.loc[
            production["Development_Concept"] == concept
        ].copy()

        concept_capex = capex.loc[
            capex["Development_Concept"] == concept,
            ["Project_Year", "CAPEX_USD"],
        ]

        if len(concept_production) != horizon:
            raise ValueError(
                f"{concept} has {len(concept_production)} production records; "
                f"expected {horizon}."
            )

        annual = concept_production.merge(
            concept_capex,
            on="Project_Year",
            how="left",
            validate="one_to_one",
        )

        annual["CAPEX_USD"] = annual["CAPEX_USD"].fillna(0.0)

        fixed_opex_rate = get_cost(opex, concept, "Fixed_OPEX")
        variable_opex_rate = get_cost(opex, concept, "Variable_OPEX")
        host_tariff_rate = get_cost(opex, concept, "Host_Tariff")
        abandonment_cost = get_cost(opex, concept, "Abandonment")

        annual["Oil_Price_USD_per_bbl"] = oil_price

        annual["Revenue_USD"] = (
            annual["Annual_Oil_Production_bbl"] * oil_price
        )

        producing = annual["Annual_Oil_Production_bbl"] > 0

        annual["Fixed_OPEX_USD"] = np.where(
            producing,
            fixed_opex_rate,
            0.0,
        )

        annual["Variable_OPEX_USD"] = (
            annual["Annual_Oil_Production_bbl"] * variable_opex_rate
        )

        annual["Host_Tariff_USD"] = (
            annual["Annual_Oil_Production_bbl"] * host_tariff_rate
        )

        annual["Total_OPEX_USD"] = (
            annual["Fixed_OPEX_USD"]
            + annual["Variable_OPEX_USD"]
            + annual["Host_Tariff_USD"]
        )

        annual["Abandonment_USD"] = np.where(
            annual["Project_Year"] == horizon,
            abandonment_cost,
            0.0,
        )

        annual["Net_Project_Cash_Flow_USD"] = (
            annual["Revenue_USD"]
            - annual["CAPEX_USD"]
            - annual["Total_OPEX_USD"]
            - annual["Abandonment_USD"]
        )

        annual["Cumulative_Net_Cash_Flow_USD"] = (
            annual["Net_Project_Cash_Flow_USD"].cumsum()
        )

        annual["Development_Concept"] = concept

        annual["Economic_Status"] = "Proposed_Illustrative"

        records.append(annual)

    result = pd.concat(records, ignore_index=True)

    result = result.sort_values(
        ["Development_Concept", "Project_Year"]
    ).reset_index(drop=True)

    PROCESSED.mkdir(parents=True, exist_ok=True)

    result.to_csv(OUTPUT_FILE, index=False)

    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"Records generated: {len(result)}")
    print(f"Oil price: ${oil_price:.2f}/bbl")
    print(f"Evaluation horizon: {horizon} years")

    print("\nEconomic summary by concept:")

    summary = (
        result.groupby("Development_Concept")
        .agg(
            Total_Production_bbl=(
                "Annual_Oil_Production_bbl", "sum"
            ),
            Total_Revenue_USD=("Revenue_USD", "sum"),
            Total_CAPEX_USD=("CAPEX_USD", "sum"),
            Total_OPEX_USD=("Total_OPEX_USD", "sum"),
            Total_Abandonment_USD=("Abandonment_USD", "sum"),
            Total_Net_Cash_Flow_USD=(
                "Net_Project_Cash_Flow_USD", "sum"
            ),
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    print("\nAnnual cash-flow sample:")

    print(
        result.loc[
            result["Project_Year"].between(1, 5),
            [
                "Development_Concept",
                "Project_Year",
                "Annual_Oil_Production_bbl",
                "Revenue_USD",
                "CAPEX_USD",
                "Total_OPEX_USD",
                "Abandonment_USD",
                "Net_Project_Cash_Flow_USD",
            ],
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
