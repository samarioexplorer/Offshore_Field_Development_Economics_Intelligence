from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"
PROCESSED = ROOT / "data" / "processed"

ASSUMPTIONS_FILE = DOCS / "economic_assumptions.csv"
CAPEX_FILE = DOCS / "development_capex_schedule.csv"
OPEX_FILE = DOCS / "operating_cost_assumptions.csv"
PRODUCTION_FILE = PROCESSED / "annual_production_profiles.csv"

OUTPUT_MODEL = PROCESSED / "scenario_annual_economic_model.csv"
OUTPUT_METRICS = PROCESSED / "scenario_investment_metrics.csv"
OUTPUT_DCF = PROCESSED / "scenario_discounted_cash_flow.csv"

SCENARIOS = {
    "Low": 55.0,
    "Base": 75.0,
    "High": 95.0,
}


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def numeric(series, label):
    try:
        return pd.to_numeric(series, errors="raise")
    except Exception as exc:
        raise ValueError(f"Non-numeric values in {label}") from exc


def load_inputs():
    assumptions = read_csv(ASSUMPTIONS_FILE)
    capex = read_csv(CAPEX_FILE)
    opex = read_csv(OPEX_FILE)
    production = read_csv(PRODUCTION_FILE)

    required = {
        "assumptions": (assumptions, {"Assumption_ID", "Parameter", "Value"}),
        "CAPEX": (capex, {"Development_Concept", "Project_Year", "CAPEX_USD"}),
        "OPEX": (opex, {"Development_Concept", "Cost_Component", "Value"}),
        "production": (
            production,
            {
                "Development_Concept", "Project_Year",
                "Annual_Oil_Production_bbl", "Producing_Year",
                "First_Oil_Year",
            },
        ),
    }
    for label, (df, columns) in required.items():
        missing = columns - set(df.columns)
        if missing:
            raise ValueError(f"{label} input missing columns: {sorted(missing)}")

    assumptions["Value"] = numeric(assumptions["Value"], "economic assumption Value")
    capex["Project_Year"] = numeric(capex["Project_Year"], "CAPEX Project_Year").astype(int)
    capex["CAPEX_USD"] = numeric(capex["CAPEX_USD"], "CAPEX_USD")
    opex["Value"] = numeric(opex["Value"], "operating cost Value")
    production["Project_Year"] = numeric(production["Project_Year"], "production Project_Year").astype(int)
    production["Annual_Oil_Production_bbl"] = numeric(
        production["Annual_Oil_Production_bbl"], "Annual_Oil_Production_bbl"
    )
    production["Producing_Year"] = numeric(production["Producing_Year"], "Producing_Year")
    production["First_Oil_Year"] = numeric(production["First_Oil_Year"], "First_Oil_Year")

    if assumptions["Assumption_ID"].duplicated().any():
        raise ValueError("Duplicate Assumption_ID values.")
    if capex.duplicated(["Development_Concept", "Project_Year"]).any():
        raise ValueError("Duplicate concept-year rows in CAPEX schedule.")
    if production.duplicated(["Development_Concept", "Project_Year"]).any():
        raise ValueError("Duplicate concept-year rows in production profiles.")

    assumption_map = dict(zip(assumptions["Assumption_ID"], assumptions["Value"]))
    for assumption_id in ("A006", "A007", "A008"):
        if assumption_id not in assumption_map:
            raise ValueError(f"Required economic assumption missing: {assumption_id}")

    return assumptions, assumption_map, capex, opex, production


def cost_value(opex, concept, component, default=0.0):
    matches = opex[
        (opex["Development_Concept"] == concept)
        & (opex["Cost_Component"].astype(str).str.strip().str.lower()
           == component.lower())
    ]
    if matches.empty:
        # Be tolerant of common underscore/space naming differences.
        normalized = opex["Cost_Component"].astype(str).str.lower().str.replace("_", " ", regex=False).str.strip()
        matches = opex[
            (opex["Development_Concept"] == concept)
            & (normalized == component.lower().replace("_", " "))
        ]
    if matches.empty:
        raise ValueError(
            f"Required OPEX component not found for {concept}/{component}. "
            "Check Cost_Component labels in operating_cost_assumptions.csv."
        )
    if len(matches) > 1:
        raise ValueError(
            f"Multiple OPEX records for {concept}/{component}; "
            "resolve duplicate cost components before modeling."
        )
    return float(matches["Value"].iloc[0])


def npv(rate, cash_flows):
    years = np.arange(1, len(cash_flows) + 1, dtype=float)
    return float(np.sum(np.asarray(cash_flows, dtype=float) / (1 + rate) ** years))


def find_irr(cash_flows):
    cash_flows = np.asarray(cash_flows, dtype=float)
    if not (np.any(cash_flows < 0) and np.any(cash_flows > 0)):
        return []

    grid = np.concatenate([
        np.linspace(-0.99, -0.50, 100),
        np.linspace(-0.50, 0.00, 200),
        np.linspace(0.00, 1.00, 400),
        np.linspace(1.00, 10.00, 200),
    ])
    roots = []
    left = float(grid[0])
    f_left = npv(left, cash_flows)

    for right_value in grid[1:]:
        right = float(right_value)
        f_right = npv(right, cash_flows)
        if f_left == 0:
            roots.append(left)
        elif f_left * f_right < 0:
            lo, hi, flo = left, right, f_left
            for _ in range(200):
                mid = (lo + hi) / 2
                fm = npv(mid, cash_flows)
                if abs(fm) < 1e-5:
                    lo = hi = mid
                    break
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
            roots.append((lo + hi) / 2)
        left, f_left = right, f_right

    unique = []
    for root in roots:
        if not any(abs(root - old) < 1e-5 for old in unique):
            unique.append(root)
    return unique


def payback_period(cash_flows, discount_rate=None):
    flows = np.asarray(cash_flows, dtype=float)
    if discount_rate is not None:
        years = np.arange(1, len(flows) + 1, dtype=float)
        flows = flows / (1 + discount_rate) ** years
    cumulative = np.cumsum(flows)
    for i, value in enumerate(cumulative):
        if value >= 0:
            previous = cumulative[i - 1] if i else 0.0
            if flows[i] == 0:
                return float(i + 1)
            fraction = -previous / flows[i]
            return float(i + fraction + 1)
    return np.nan


def build_annual_model(assumption_map, capex, opex, production, horizon):
    rows = []
    concepts = sorted(production["Development_Concept"].unique())

    for concept in concepts:
        prod = production[production["Development_Concept"] == concept].copy()
        prod = prod.sort_values("Project_Year")
        if len(prod) != horizon or prod["Project_Year"].tolist() != list(range(1, horizon + 1)):
            raise ValueError(f"{concept}: production profiles must contain years 1..{horizon}.")

        concept_capex = capex[capex["Development_Concept"] == concept]
        capex_by_year = concept_capex.groupby("Project_Year")["CAPEX_USD"].sum().to_dict()

        fixed_opex = cost_value(opex, concept, "Fixed_OPEX")
        variable_opex = cost_value(opex, concept, "Variable_OPEX")
        host_tariff = cost_value(opex, concept, "Host_Tariff")
        abandonment = cost_value(opex, concept, "Abandonment")

        for _, p in prod.iterrows():
            year = int(p["Project_Year"])
            volume = float(p["Annual_Oil_Production_bbl"])
            producing = volume > 0
            capex_value = float(capex_by_year.get(year, 0.0))
            revenue_base = volume * float(assumption_map["A005"])
            fixed_value = fixed_opex if producing else 0.0
            variable_value = volume * variable_opex
            tariff_value = volume * host_tariff
            abandonment_value = abandonment if year == horizon else 0.0
            total_opex = fixed_value + variable_value + tariff_value
            net_cf = revenue_base - capex_value - total_opex - abandonment_value

            row = p.to_dict()
            row.update({
                "CAPEX_USD": capex_value,
                "Fixed_OPEX_USD": fixed_value,
                "Variable_OPEX_USD": variable_value,
                "Host_Tariff_USD": tariff_value,
                "Total_OPEX_USD": total_opex,
                "Abandonment_USD": abandonment_value,
            })
            # Scenario-specific revenue/cash flow fields are added below.
            rows.append(row)

    base = pd.DataFrame(rows)
    scenario_rows = []
    for scenario_name, price in SCENARIOS.items():
        temp = base.copy()
        temp["Oil_Price_Scenario"] = scenario_name
        temp["Oil_Price_USD_per_bbl"] = price
        temp["Revenue_USD"] = temp["Annual_Oil_Production_bbl"] * price
        temp["Net_Project_Cash_Flow_USD"] = (
            temp["Revenue_USD"]
            - temp["CAPEX_USD"]
            - temp["Total_OPEX_USD"]
            - temp["Abandonment_USD"]
        )
        temp["Economic_Status"] = "Proposed_Illustrative"
        scenario_rows.append(temp)

    return pd.concat(scenario_rows, ignore_index=True)


def build_metrics_and_dcf(scenario_model, discount_rate, horizon):
    metric_rows, dcf_rows = [], []
    for (concept, scenario), group in scenario_model.groupby(
        ["Development_Concept", "Oil_Price_Scenario"], sort=True
    ):
        group = group.sort_values("Project_Year").copy()
        flows = group["Net_Project_Cash_Flow_USD"].to_numpy(dtype=float)
        years = group["Project_Year"].to_numpy(dtype=int)
        discounted = flows / (1 + discount_rate) ** years
        cum_undiscounted = np.cumsum(flows)
        cum_discounted = np.cumsum(discounted)
        roots = find_irr(flows)

        if len(roots) == 1:
            irr = roots[0]
            irr_status = "Single numerical root found"
        elif len(roots) > 1:
            irr = np.nan
            irr_status = "Multiple roots found: " + ", ".join(f"{r:.12f}" for r in roots)
        else:
            irr = np.nan
            irr_status = "No IRR root identified in search range (-0.99, 10.0)"

        production = group["Annual_Oil_Production_bbl"].to_numpy(dtype=float)
        costs = (
            group["CAPEX_USD"].to_numpy(dtype=float)
            + group["Total_OPEX_USD"].to_numpy(dtype=float)
            + group["Abandonment_USD"].to_numpy(dtype=float)
        )
        discounted_production = np.sum(production / (1 + discount_rate) ** years)
        discounted_costs = np.sum(costs / (1 + discount_rate) ** years)
        breakeven = discounted_costs / discounted_production if discounted_production > 0 else np.nan

        metric_rows.append({
            "Development_Concept": concept,
            "Oil_Price_Scenario": scenario,
            "Oil_Price_USD_per_bbl": float(group["Oil_Price_USD_per_bbl"].iloc[0]),
            "Discount_Rate": discount_rate,
            "Evaluation_Horizon_Years": horizon,
            "Total_Production_bbl": float(production.sum()),
            "Total_Revenue_USD": float(group["Revenue_USD"].sum()),
            "Total_CAPEX_USD": float(group["CAPEX_USD"].sum()),
            "Total_OPEX_USD": float(group["Total_OPEX_USD"].sum()),
            "Total_Abandonment_USD": float(group["Abandonment_USD"].sum()),
            "Undiscounted_Net_Cash_Flow_USD": float(flows.sum()),
            "NPV_USD": float(discounted.sum()),
            "IRR": float(irr) if np.isfinite(irr) else np.nan,
            "IRR_Status": irr_status,
            "Undiscounted_Payback_Year": payback_period(flows),
            "Discounted_Payback_Year": payback_period(flows, discount_rate),
            "Breakeven_Oil_Price_USD_per_bbl": float(breakeven),
            "Economic_Status": "Proposed_Illustrative",
        })

        for i, year in enumerate(years):
            dcf_rows.append({
                "Development_Concept": concept,
                "Oil_Price_Scenario": scenario,
                "Oil_Price_USD_per_bbl": float(group["Oil_Price_USD_per_bbl"].iloc[i]),
                "Project_Year": int(year),
                "Net_Project_Cash_Flow_USD": float(flows[i]),
                "Discount_Rate": discount_rate,
                "Discount_Factor": float(1 / (1 + discount_rate) ** year),
                "Discounted_Cash_Flow_USD": float(discounted[i]),
                "Cumulative_Discounted_Cash_Flow_USD": float(cum_discounted[i]),
                "Cumulative_Undiscounted_Cash_Flow_USD": float(cum_undiscounted[i]),
            })
    return pd.DataFrame(metric_rows), pd.DataFrame(dcf_rows)


def main():
    print("=" * 78)
    print("PROJECT 3 — OIL-PRICE SCENARIO ENGINE")
    print("=" * 78)

    assumptions, amap, capex, opex, production = load_inputs()
    discount_rate = float(amap["A006"])
    horizon = int(amap["A007"])
    base_price = float(amap["A005"])

    if not np.isclose(SCENARIOS["Base"], base_price):
        raise ValueError(
            f"Base scenario (${SCENARIOS['Base']}) does not match A005 (${base_price})."
        )
    if not (0 <= discount_rate < 1):
        raise ValueError("Discount rate must be between 0 (inclusive) and 1 (exclusive).")
    if set(production["Development_Concept"].unique()) != {"Standalone_FPSO", "Subsea_Tieback"}:
        raise ValueError("Unexpected development concept set in production profiles.")

    scenario_model = build_annual_model(amap, capex, opex, production, horizon)
    metrics, dcf = build_metrics_and_dcf(scenario_model, discount_rate, horizon)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    scenario_model.to_csv(OUTPUT_MODEL, index=False)
    metrics.to_csv(OUTPUT_METRICS, index=False)
    dcf.to_csv(OUTPUT_DCF, index=False)

    print(f"\nScenario annual model: {OUTPUT_MODEL}")
    print(f"Scenario investment metrics: {OUTPUT_METRICS}")
    print(f"Scenario discounted cash flow: {OUTPUT_DCF}")
    print("\nInvestment metrics by scenario:")
    display_cols = [
        "Development_Concept", "Oil_Price_Scenario", "Oil_Price_USD_per_bbl",
        "NPV_USD", "IRR", "Undiscounted_Payback_Year",
        "Discounted_Payback_Year", "Breakeven_Oil_Price_USD_per_bbl",
    ]
    print(metrics[display_cols].to_string(index=False, formatters={
        "NPV_USD": lambda x: f"${x:,.0f}",
        "IRR": lambda x: f"{x:.2%}" if pd.notna(x) else "N/A",
        "Undiscounted_Payback_Year": lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
        "Discounted_Payback_Year": lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
        "Breakeven_Oil_Price_USD_per_bbl": lambda x: f"${x:.2f}",
    }))
    print("\nRecord counts:")
    print(f"Annual scenario model: {len(scenario_model)} (expected 150)")
    print(f"Investment metrics: {len(metrics)} (expected 6)")
    print(f"Discounted cash flow: {len(dcf)} (expected 150)")
    print("\nScenario generation complete. Run the independent validation script next.")


if __name__ == "__main__":
    main()
