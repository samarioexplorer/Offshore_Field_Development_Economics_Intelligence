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
BASE_MODEL_FILE = PROCESSED / "annual_economic_model.csv"
BASE_METRICS_FILE = PROCESSED / "investment_metrics.csv"

SCENARIO_MODEL_FILE = PROCESSED / "scenario_annual_economic_model.csv"
SCENARIO_METRICS_FILE = PROCESSED / "scenario_investment_metrics.csv"
SCENARIO_DCF_FILE = PROCESSED / "scenario_discounted_cash_flow.csv"

SCENARIOS = {"Low": 55.0, "Base": 75.0, "High": 95.0}
TOL = 1e-5
checks = []


def check(name, condition, detail=""):
    passed = bool(condition)
    checks.append((name, passed, detail))
    print(f"{'PASS' if passed else 'FAIL'} | {name}" + (f" | {detail}" if detail else ""))


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input/output not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def load_assumptions():
    df = read_csv(ASSUMPTIONS_FILE)
    df["Value"] = pd.to_numeric(df["Value"], errors="raise")
    if df["Assumption_ID"].duplicated().any():
        raise ValueError("Duplicate assumption IDs.")
    return dict(zip(df["Assumption_ID"], df["Value"]))


def npv(rate, flows):
    years = np.arange(1, len(flows) + 1, dtype=float)
    return float(np.sum(np.asarray(flows, dtype=float) / (1 + rate) ** years))


def payback(flows, rate=None):
    flows = np.asarray(flows, dtype=float)
    if rate is not None:
        flows = flows / (1 + rate) ** np.arange(1, len(flows) + 1, dtype=float)
    cumulative = np.cumsum(flows)
    for i, value in enumerate(cumulative):
        if value >= 0:
            previous = cumulative[i - 1] if i else 0.0
            if flows[i] == 0:
                return float(i + 1)
            return float(i + (-previous / flows[i]) + 1)
    return np.nan


def get_cost(opex, concept, component):
    normalized = opex["Cost_Component"].astype(str).str.lower().str.replace("_", " ", regex=False).str.strip()
    target = component.lower().replace("_", " ")
    rows = opex[(opex["Development_Concept"] == concept) & (normalized == target)]
    if rows.empty:
        raise ValueError(
            f"Required OPEX component not found for {concept}/{component}. "
            "Check Cost_Component labels in operating_cost_assumptions.csv."
        )
    if len(rows) != 1:
        raise ValueError(f"Expected one OPEX value for {concept}/{component}, found {len(rows)}")
    return float(rows["Value"].iloc[0])


def main():
    print("=" * 78)
    print("PROJECT 3 — INDEPENDENT OIL-PRICE SCENARIO QA")
    print("=" * 78)

    assumptions = load_assumptions()
    capex = read_csv(CAPEX_FILE)
    opex = read_csv(OPEX_FILE)
    production = read_csv(PRODUCTION_FILE)
    base_model = read_csv(BASE_MODEL_FILE)
    base_metrics = read_csv(BASE_METRICS_FILE)
    model = read_csv(SCENARIO_MODEL_FILE)
    metrics = read_csv(SCENARIO_METRICS_FILE)
    dcf = read_csv(SCENARIO_DCF_FILE)

    rate = float(assumptions["A006"])
    horizon = int(assumptions["A007"])
    base_price = float(assumptions["A005"])
    concepts = sorted(production["Development_Concept"].unique())
    expected_keys = {(c, s) for c in concepts for s in SCENARIOS}
    key_columns = ["Development_Concept", "Oil_Price_Scenario"]
    year_keys = ["Development_Concept", "Oil_Price_Scenario", "Project_Year"]

    check("QA-01 Scenario outputs exist", True, "All required scenario outputs loaded")
    check("QA-02 Expected scenario prices", set(SCENARIOS.values()) == {55.0, 75.0, 95.0} and SCENARIOS["Base"] == base_price,
          f"Low=${SCENARIOS['Low']:.0f}, Base=${SCENARIOS['Base']:.0f}, High=${SCENARIOS['High']:.0f}; A005=${base_price:.2f}")
    check("QA-03 Expected row counts", len(model) == 150 and len(metrics) == 6 and len(dcf) == 150,
          f"annual={len(model)}/150; metrics={len(metrics)}/6; DCF={len(dcf)}/150")
    check("QA-04 Complete concept-scenario coverage",
          set(map(tuple, metrics[key_columns].drop_duplicates().to_numpy())) == expected_keys
          and set(map(tuple, model[key_columns].drop_duplicates().to_numpy())) == expected_keys,
          "Two concepts × three scenarios")
    check("QA-05 No duplicate concept-scenario-year keys",
          not model.duplicated(year_keys).any() and not dcf.duplicated(year_keys).any(),
          f"annual duplicates={int(model.duplicated(year_keys).sum())}; DCF duplicates={int(dcf.duplicated(year_keys).sum())}")
    check("QA-06 Complete year sequences",
          all(sorted(g["Project_Year"].astype(int).tolist()) == list(range(1, horizon + 1))
              for _, g in model.groupby(key_columns))
          and all(sorted(g["Project_Year"].astype(int).tolist()) == list(range(1, horizon + 1))
                  for _, g in dcf.groupby(key_columns)),
          f"Years 1 through {horizon} for all six cases")

    numeric_model = [
        "Oil_Price_USD_per_bbl", "Annual_Oil_Production_bbl", "CAPEX_USD",
        "Fixed_OPEX_USD", "Variable_OPEX_USD", "Host_Tariff_USD",
        "Total_OPEX_USD", "Abandonment_USD", "Revenue_USD",
        "Net_Project_Cash_Flow_USD",
    ]
    numeric_metrics = [
        "Oil_Price_USD_per_bbl", "NPV_USD", "Total_Production_bbl",
        "Total_Revenue_USD", "Total_CAPEX_USD", "Total_OPEX_USD",
        "Total_Abandonment_USD", "Undiscounted_Net_Cash_Flow_USD",
        "Breakeven_Oil_Price_USD_per_bbl",
    ]
    finite_model = np.isfinite(model[numeric_model].to_numpy(dtype=float)).all()
    finite_metrics = np.isfinite(metrics[numeric_metrics].to_numpy(dtype=float)).all()
    check("QA-07 Required numeric fields are finite", finite_model and finite_metrics,
          "NaN/inf not allowed in core model or metrics fields")

    # Independently reconstruct annual costs and revenue from source registers.
    capex_grouped = capex.groupby(["Development_Concept", "Project_Year"])["CAPEX_USD"].sum().to_dict()
    source_production = production.set_index(["Development_Concept", "Project_Year"])["Annual_Oil_Production_bbl"].to_dict()
    reconstructed_ok = True
    for _, row in model.iterrows():
        concept, year = row["Development_Concept"], int(row["Project_Year"])
        volume = float(source_production[(concept, year)])
        fixed = get_cost(opex, concept, "Fixed_OPEX") if volume > 0 else 0.0
        variable = volume * get_cost(opex, concept, "Variable_OPEX")
        tariff = volume * get_cost(opex, concept, "Host_Tariff")
        abandon = get_cost(opex, concept, "Abandonment") if year == horizon else 0.0
        capex_value = float(capex_grouped.get((concept, year), 0.0))
        price = SCENARIOS[row["Oil_Price_Scenario"]]
        expected = {
            "Annual_Oil_Production_bbl": volume,
            "CAPEX_USD": capex_value,
            "Fixed_OPEX_USD": fixed,
            "Variable_OPEX_USD": variable,
            "Host_Tariff_USD": tariff,
            "Total_OPEX_USD": fixed + variable + tariff,
            "Abandonment_USD": abandon,
            "Revenue_USD": volume * price,
            "Net_Project_Cash_Flow_USD": volume * price - capex_value - fixed - variable - tariff - abandon,
        }
        for col, val in expected.items():
            if not np.isclose(float(row[col]), val, rtol=1e-9, atol=0.02):
                reconstructed_ok = False
                break
        if not reconstructed_ok:
            break
    check("QA-08 Annual scenario model independently reconstructs from source inputs",
          reconstructed_ok, "Production, CAPEX, cost components, revenue, and net cash flow")

    # Price should only affect revenue and net cash flow, not volume or cost assumptions.
    fixed_costs_ok = True
    for _, group in model.groupby(["Development_Concept", "Project_Year"]):
        for col in ["Annual_Oil_Production_bbl", "CAPEX_USD", "Fixed_OPEX_USD",
                    "Variable_OPEX_USD", "Host_Tariff_USD", "Total_OPEX_USD", "Abandonment_USD"]:
            if not np.allclose(group[col].to_numpy(dtype=float), group[col].iloc[0], rtol=1e-10, atol=0.01):
                fixed_costs_ok = False
    check("QA-09 Scenario changes do not alter production or costs", fixed_costs_ok,
          "Oil price affects revenue and net cash flow only")

    # Independent metric calculations for each concept/scenario.
    metrics_ok = True
    dcf_ok = True
    for _, m in metrics.iterrows():
        concept, scenario = m["Development_Concept"], m["Oil_Price_Scenario"]
        g = model[(model["Development_Concept"] == concept) & (model["Oil_Price_Scenario"] == scenario)].sort_values("Project_Year")
        flows = g["Net_Project_Cash_Flow_USD"].to_numpy(dtype=float)
        years = g["Project_Year"].to_numpy(dtype=int)
        expected_npv = npv(rate, flows)
        if not np.isclose(float(m["NPV_USD"]), expected_npv, rtol=1e-9, atol=0.05):
            metrics_ok = False
        if not np.isclose(float(m["Total_Production_bbl"]), g["Annual_Oil_Production_bbl"].sum(), rtol=1e-9, atol=0.01):
            metrics_ok = False
        for col in ["Revenue_USD", "CAPEX_USD", "Total_OPEX_USD", "Abandonment_USD"]:
            target = {
                "Revenue_USD": "Total_Revenue_USD",
                "CAPEX_USD": "Total_CAPEX_USD",
                "Total_OPEX_USD": "Total_OPEX_USD",
                "Abandonment_USD": "Total_Abandonment_USD",
            }[col]
            if not np.isclose(float(m[target]), g[col].sum(), rtol=1e-9, atol=0.05):
                metrics_ok = False
        if not np.isclose(float(m["Undiscounted_Net_Cash_Flow_USD"]), flows.sum(), rtol=1e-9, atol=0.05):
            metrics_ok = False
        expected_irr = float(m["IRR"]) if pd.notna(m["IRR"]) else np.nan
        if np.isfinite(expected_irr) and abs(npv(expected_irr, flows)) > 1.0:
            metrics_ok = False
        if not np.isclose(float(m["Undiscounted_Payback_Year"]), payback(flows), rtol=1e-8, atol=1e-5):
            metrics_ok = False
        if not np.isclose(float(m["Discounted_Payback_Year"]), payback(flows, rate), rtol=1e-8, atol=1e-5):
            metrics_ok = False

        volume = g["Annual_Oil_Production_bbl"].to_numpy(dtype=float)
        costs = g["CAPEX_USD"].to_numpy(dtype=float) + g["Total_OPEX_USD"].to_numpy(dtype=float) + g["Abandonment_USD"].to_numpy(dtype=float)
        breakeven = np.sum(costs / (1 + rate) ** years) / np.sum(volume / (1 + rate) ** years)
        if not np.isclose(float(m["Breakeven_Oil_Price_USD_per_bbl"]), breakeven, rtol=1e-9, atol=1e-7):
            metrics_ok = False
        if not np.isclose(npv(rate, volume * breakeven - costs), 0.0, atol=0.05):
            metrics_ok = False

        dg = dcf[(dcf["Development_Concept"] == concept) & (dcf["Oil_Price_Scenario"] == scenario)].sort_values("Project_Year")
        disc = flows / (1 + rate) ** years
        if not np.allclose(dg["Net_Project_Cash_Flow_USD"], flows, rtol=1e-9, atol=0.05):
            dcf_ok = False
        if not np.allclose(dg["Discount_Factor"], 1 / (1 + rate) ** years, rtol=1e-9, atol=1e-12):
            dcf_ok = False
        if not np.allclose(dg["Discounted_Cash_Flow_USD"], disc, rtol=1e-9, atol=0.05):
            dcf_ok = False
        if not np.allclose(dg["Cumulative_Discounted_Cash_Flow_USD"], np.cumsum(disc), rtol=1e-9, atol=0.05):
            dcf_ok = False
        if not np.allclose(dg["Cumulative_Undiscounted_Cash_Flow_USD"], np.cumsum(flows), rtol=1e-9, atol=0.05):
            dcf_ok = False

    check("QA-10 Investment metrics independently reconcile", metrics_ok,
          "NPV, IRR, payback, breakeven, and economic totals")
    check("QA-11 Discounted cash-flow schedule independently reconciles", dcf_ok,
          "Discount factors, annual discounted cash flows, and cumulative values")

    # NPV should rise as oil price rises, while breakeven is scenario-invariant.
    monotonic_ok = True
    breakeven_constant_ok = True
    for concept, group in metrics.groupby("Development_Concept"):
        ordered = group.set_index("Oil_Price_Scenario").loc[["Low", "Base", "High"]]
        if not (ordered["NPV_USD"].iloc[0] < ordered["NPV_USD"].iloc[1] < ordered["NPV_USD"].iloc[2]):
            monotonic_ok = False
        if ordered["Breakeven_Oil_Price_USD_per_bbl"].max() - ordered["Breakeven_Oil_Price_USD_per_bbl"].min() > 1e-6:
            breakeven_constant_ok = False
    check("QA-12 NPV increases with oil-price scenario", monotonic_ok,
          "Low NPV < Base NPV < High NPV for each concept")
    check("QA-13 Breakeven price is scenario-invariant", breakeven_constant_ok,
          "Production and costs are held constant across price scenarios")

    # Base scenario must reconcile to existing base-case model/metrics.
    base_scenario = model[model["Oil_Price_Scenario"] == "Base"]
    base_case_ok = True
    if len(base_scenario) != len(base_model):
        base_case_ok = False
    else:
        merge = base_scenario.merge(
            base_model,
            on=["Development_Concept", "Project_Year"],
            suffixes=("_scenario", "_base"),
            how="outer",
            indicator=True,
        )
        if not (merge["_merge"] == "both").all():
            base_case_ok = False
        else:
            for col in ["Revenue_USD", "CAPEX_USD", "Total_OPEX_USD", "Abandonment_USD", "Net_Project_Cash_Flow_USD"]:
                a, b = f"{col}_scenario", f"{col}_base"
                if a in merge.columns and b in merge.columns and not np.allclose(merge[a], merge[b], rtol=1e-9, atol=0.05):
                    base_case_ok = False
    base_metrics_ok = True
    for _, bm in base_metrics.iterrows():
        match = metrics[(metrics["Development_Concept"] == bm["Development_Concept"]) & (metrics["Oil_Price_Scenario"] == "Base")]
        if len(match) != 1 or not np.isclose(float(match["NPV_USD"].iloc[0]), float(bm["NPV_USD"]), rtol=1e-9, atol=0.05):
            base_metrics_ok = False
    check("QA-14 Base scenario reconciles to existing economic model", base_case_ok,
          "Scenario Base at $75/bbl matches annual_economic_model.csv")
    check("QA-15 Base scenario NPV reconciles to existing metrics", base_metrics_ok,
          "Scenario Base NPV matches investment_metrics.csv")

    status_ok = set(model["Economic_Status"].dropna().unique()) == {"Proposed_Illustrative"} and set(metrics["Economic_Status"].dropna().unique()) == {"Proposed_Illustrative"}
    check("QA-16 Illustrative status is retained", status_ok,
          "Outputs remain explicitly classified Proposed_Illustrative")

    print("\n" + "=" * 78)
    passed = sum(1 for _, ok, _ in checks if ok)
    failed = len(checks) - passed
    print(f"SUMMARY: {passed} PASSED | {failed} FAILED | {len(checks)} TOTAL")
    print("=" * 78)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
