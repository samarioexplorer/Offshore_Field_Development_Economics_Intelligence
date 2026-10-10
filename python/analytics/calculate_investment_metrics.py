from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DOCS = ROOT / "documentation"
PROCESSED = ROOT / "data" / "processed"

MODEL_FILE = PROCESSED / "annual_economic_model.csv"
ASSUMPTIONS_FILE = DOCS / "economic_assumptions.csv"

OUTPUT_FILE = PROCESSED / "investment_metrics.csv"
DCF_FILE = PROCESSED / "discounted_cash_flow.csv"


def load_assumptions():
    df = pd.read_csv(ASSUMPTIONS_FILE, encoding="utf-8-sig")
    df["Value"] = pd.to_numeric(df["Value"], errors="raise")

    if df["Assumption_ID"].duplicated().any():
        raise ValueError("Duplicate economic assumption IDs.")

    return dict(zip(df["Assumption_ID"], df["Value"]))


def npv(rate, cash_flows):
    years = np.arange(1, len(cash_flows) + 1)

    return float(
        np.sum(cash_flows / ((1 + rate) ** years))
    )


def find_irr(cash_flows):
    """
    Find an economically meaningful IRR when a solution exists.

    Uses a numerical scan to locate sign changes in NPV, followed
    by bisection. Multiple IRRs are reported rather than silently
    selecting one.
    """
    if not (
        np.any(cash_flows < 0)
        and np.any(cash_flows > 0)
    ):
        return []

    def npv_function(rate):
        return npv(rate, cash_flows)

    grid = np.concatenate(
        [
            np.linspace(-0.99, -0.50, 100),
            np.linspace(-0.50, 0.00, 200),
            np.linspace(0.00, 1.00, 400),
            np.linspace(1.00, 10.00, 200),
        ]
    )

    roots = []

    previous_rate = grid[0]
    previous_value = npv_function(previous_rate)

    for current_rate in grid[1:]:
        current_value = npv_function(current_rate)

        if current_value == 0:
            roots.append(current_rate)
        elif previous_value * current_value < 0:
            low = previous_rate
            high = current_rate
            low_value = previous_value

            for _ in range(200):
                mid = (low + high) / 2
                mid_value = npv_function(mid)

                if abs(mid_value) < 1e-7:
                    low = high = mid
                    break

                if low_value * mid_value <= 0:
                    high = mid
                else:
                    low = mid
                    low_value = mid_value

            roots.append((low + high) / 2)

        previous_rate = current_rate
        previous_value = current_value

    unique_roots = []

    for root in roots:
        if not any(abs(root - existing) < 1e-5 for existing in unique_roots):
            unique_roots.append(root)

    return unique_roots


def payback_period(cash_flows, discount_rate=None):
    """
    Return the fractional year in which cumulative cash flow
    first becomes non-negative.

    Returns None if payback is not achieved within the horizon.
    """
    cash_flows = np.asarray(cash_flows, dtype=float)

    if discount_rate is not None:
        years = np.arange(1, len(cash_flows) + 1)
        cash_flows = cash_flows / ((1 + discount_rate) ** years)

    cumulative = np.cumsum(cash_flows)

    for index, value in enumerate(cumulative):
        if value >= 0:
            previous = cumulative[index - 1] if index > 0 else 0.0
            annual_flow = cash_flows[index]

            if annual_flow == 0:
                return float(index + 1)

            fraction = -previous / annual_flow

            return float(index + fraction + 1)

    return None


def breakeven_oil_price(group, discount_rate):
    """
    Calculate the constant oil price that produces zero NPV.

    Production is held fixed. All modeled costs remain unchanged.
    """
    production = group["Annual_Oil_Production_bbl"].to_numpy(dtype=float)

    costs = (
        group["CAPEX_USD"].to_numpy(dtype=float)
        + group["Total_OPEX_USD"].to_numpy(dtype=float)
        + group["Abandonment_USD"].to_numpy(dtype=float)
    )

    discounted_production = np.sum(
        production
        / ((1 + discount_rate) ** np.arange(1, len(production) + 1))
    )

    discounted_costs = np.sum(
        costs
        / ((1 + discount_rate) ** np.arange(1, len(costs) + 1))
    )

    if discounted_production <= 0:
        return None

    return float(discounted_costs / discounted_production)


def main():
    print("=" * 72)
    print("PROJECT 3 — INVESTMENT ECONOMICS")
    print("=" * 72)

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Annual economic model not found: {MODEL_FILE}"
        )

    model = pd.read_csv(MODEL_FILE, encoding="utf-8-sig")
    assumptions = load_assumptions()

    discount_rate = float(assumptions["A006"])
    horizon = int(assumptions["A007"])

    records = []
    dcf_records = []

    for concept, group in model.groupby("Development_Concept"):
        group = group.sort_values("Project_Year").copy()

        if len(group) != horizon:
            raise ValueError(
                f"{concept}: expected {horizon} annual records, "
                f"found {len(group)}."
            )

        if group["Project_Year"].tolist() != list(range(1, horizon + 1)):
            raise ValueError(
                f"{concept}: project-year sequence is incomplete."
            )

        cash_flows = group[
            "Net_Project_Cash_Flow_USD"
        ].to_numpy(dtype=float)

        years = group["Project_Year"].to_numpy(dtype=int)

        discounted_flows = cash_flows / (
            (1 + discount_rate) ** years
        )

        cumulative_undiscounted = np.cumsum(cash_flows)
        cumulative_discounted = np.cumsum(discounted_flows)

        project_npv = float(discounted_flows.sum())

        irr_roots = find_irr(cash_flows)

        if len(irr_roots) == 1:
            irr_value = irr_roots[0]
            irr_status = "Single numerical root found"
        elif len(irr_roots) > 1:
            irr_value = np.nan
            irr_status = (
                f"Multiple roots found: "
                f"{', '.join(f'{x:.6f}' for x in irr_roots)}"
            )
        else:
            irr_value = np.nan
            irr_status = "No IRR root identified in the search range"

        breakeven = breakeven_oil_price(
            group,
            discount_rate,
        )

        records.append(
            {
                "Development_Concept": concept,
                "Oil_Price_USD_per_bbl": float(
                    group["Oil_Price_USD_per_bbl"].iloc[0]
                ),
                "Discount_Rate": discount_rate,
                "Evaluation_Horizon_Years": horizon,
                "Total_Production_bbl": float(
                    group["Annual_Oil_Production_bbl"].sum()
                ),
                "Total_Revenue_USD": float(
                    group["Revenue_USD"].sum()
                ),
                "Total_CAPEX_USD": float(
                    group["CAPEX_USD"].sum()
                ),
                "Total_OPEX_USD": float(
                    group["Total_OPEX_USD"].sum()
                ),
                "Total_Abandonment_USD": float(
                    group["Abandonment_USD"].sum()
                ),
                "Undiscounted_Net_Cash_Flow_USD": float(
                    cash_flows.sum()
                ),
                "NPV_USD": project_npv,
                "IRR": irr_value,
                "IRR_Status": irr_status,
                "Undiscounted_Payback_Year": payback_period(
                    cash_flows
                ),
                "Discounted_Payback_Year": payback_period(
                    cash_flows,
                    discount_rate,
                ),
                "Breakeven_Oil_Price_USD_per_bbl": breakeven,
                "Economic_Status": "Proposed_Illustrative",
            }
        )

        for index, year in enumerate(years):
            dcf_records.append(
                {
                    "Development_Concept": concept,
                    "Project_Year": int(year),
                    "Net_Project_Cash_Flow_USD": float(
                        cash_flows[index]
                    ),
                    "Discount_Rate": discount_rate,
                    "Discount_Factor": float(
                        1 / ((1 + discount_rate) ** year)
                    ),
                    "Discounted_Cash_Flow_USD": float(
                        discounted_flows[index]
                    ),
                    "Cumulative_Discounted_Cash_Flow_USD": float(
                        cumulative_discounted[index]
                    ),
                    "Cumulative_Undiscounted_Cash_Flow_USD": float(
                        cumulative_undiscounted[index]
                    ),
                }
            )

    metrics = pd.DataFrame(records)
    dcf = pd.DataFrame(dcf_records)

    PROCESSED.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(OUTPUT_FILE, index=False)
    dcf.to_csv(DCF_FILE, index=False)

    print(f"\nMetrics output: {OUTPUT_FILE}")
    print(f"DCF output: {DCF_FILE}")

    print("\nInvestment metrics:")
    print(metrics.to_string(index=False))

    print("\nDiscounted cash-flow reconciliation:")

    reconciliation = (
        dcf.groupby("Development_Concept")
        .agg(
            Sum_Discounted_Cash_Flow_USD=(
                "Discounted_Cash_Flow_USD",
                "sum",
            ),
            Final_Cumulative_Discounted_Cash_Flow_USD=(
                "Cumulative_Discounted_Cash_Flow_USD",
                "last",
            ),
        )
        .reset_index()
    )

    print(reconciliation.to_string(index=False))


if __name__ == "__main__":
    main()
