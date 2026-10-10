from pathlib import Path
import math
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "documentation"
PROCESSED = ROOT / "data" / "processed"

ASSUMPTIONS_FILE = DOCS / "economic_assumptions.csv"
MODEL_FILE = PROCESSED / "annual_economic_model.csv"
METRICS_FILE = PROCESSED / "investment_metrics.csv"
DCF_FILE = PROCESSED / "discounted_cash_flow.csv"

TOL_USD = 1.00
TOL_PRICE = 1e-6
TOL_RATE = 1e-5
TOL_YEAR = 1e-5

checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), str(detail)))


def near(a, b, atol=TOL_USD, rtol=1e-9):
    try:
        return bool(np.isclose(float(a), float(b), atol=atol, rtol=rtol, equal_nan=False))
    except (TypeError, ValueError):
        return False


def calculate_npv(rate, cash_flows):
    years = np.arange(1, len(cash_flows) + 1, dtype=float)
    return float(np.sum(np.asarray(cash_flows, dtype=float) / (1.0 + rate) ** years))


def calculate_payback(cash_flows, rate=None):
    flows = np.asarray(cash_flows, dtype=float)
    if rate is not None:
        years = np.arange(1, len(flows) + 1, dtype=float)
        flows = flows / (1.0 + rate) ** years
    cumulative = np.cumsum(flows)
    for i, value in enumerate(cumulative):
        if value >= 0:
            previous = cumulative[i - 1] if i else 0.0
            annual_flow = flows[i]
            if annual_flow == 0:
                return float(i + 1)
            fraction = -previous / annual_flow
            return float(i + fraction + 1)
    return None


def calculate_breakeven_price(group, rate):
    years = group["Project_Year"].to_numpy(dtype=float)
    production = group["Annual_Oil_Production_bbl"].to_numpy(dtype=float)
    costs = (
        group["CAPEX_USD"].to_numpy(dtype=float)
        + group["Total_OPEX_USD"].to_numpy(dtype=float)
        + group["Abandonment_USD"].to_numpy(dtype=float)
    )
    discount_factors = (1.0 + rate) ** years
    discounted_production = float(np.sum(production / discount_factors))
    discounted_costs = float(np.sum(costs / discount_factors))
    if discounted_production <= 0:
        return None
    return discounted_costs / discounted_production


def main():
    print("=" * 78)
    print("PROJECT 3 — INDEPENDENT INVESTMENT-METRICS QA")
    print("=" * 78)
    print(f"Project root: {ROOT}")

    required_files = [ASSUMPTIONS_FILE, MODEL_FILE, METRICS_FILE, DCF_FILE]
    missing = [p for p in required_files if not p.exists()]
    record("QA-01 Required source/output files exist", not missing,
           "Missing: " + ", ".join(str(p) for p in missing) if missing else "All four files found")
    if missing:
        for name, passed, detail in checks:
            print(f"{'PASS' if passed else 'FAIL'} | {name} | {detail}")
        print("\nCannot continue because one or more required files are missing.")
        sys.exit(1)

    assumptions_df = pd.read_csv(ASSUMPTIONS_FILE, encoding="utf-8-sig")
    model = pd.read_csv(MODEL_FILE, encoding="utf-8-sig")
    metrics = pd.read_csv(METRICS_FILE, encoding="utf-8-sig")
    dcf = pd.read_csv(DCF_FILE, encoding="utf-8-sig")

    required_assumption_cols = {"Assumption_ID", "Value"}
    required_model_cols = {
        "Development_Concept", "Project_Year", "Annual_Oil_Production_bbl",
        "Oil_Price_USD_per_bbl", "Revenue_USD", "CAPEX_USD",
        "Total_OPEX_USD", "Abandonment_USD", "Net_Project_Cash_Flow_USD",
    }
    required_metric_cols = {
        "Development_Concept", "Oil_Price_USD_per_bbl", "Discount_Rate",
        "Evaluation_Horizon_Years", "Total_Production_bbl", "Total_Revenue_USD",
        "Total_CAPEX_USD", "Total_OPEX_USD", "Total_Abandonment_USD",
        "Undiscounted_Net_Cash_Flow_USD", "NPV_USD", "IRR", "IRR_Status",
        "Undiscounted_Payback_Year", "Discounted_Payback_Year",
        "Breakeven_Oil_Price_USD_per_bbl",
    }
    required_dcf_cols = {
        "Development_Concept", "Project_Year", "Net_Project_Cash_Flow_USD",
        "Discount_Rate", "Discount_Factor", "Discounted_Cash_Flow_USD",
        "Cumulative_Discounted_Cash_Flow_USD", "Cumulative_Undiscounted_Cash_Flow_USD",
    }
    record("QA-02 Required columns present", required_assumption_cols.issubset(assumptions_df.columns)
           and required_model_cols.issubset(model.columns)
           and required_metric_cols.issubset(metrics.columns)
           and required_dcf_cols.issubset(dcf.columns), "Checked assumptions, model, metrics, and DCF schemas")

    try:
        if assumptions_df["Assumption_ID"].duplicated().any():
            raise ValueError("Duplicate assumption IDs")
        assumptions_df["Value"] = pd.to_numeric(assumptions_df["Value"], errors="raise")
        assumptions = dict(zip(assumptions_df["Assumption_ID"], assumptions_df["Value"]))
        rate = float(assumptions["A006"])
        horizon = int(assumptions["A007"])
        base_price = float(assumptions["A005"])
        record("QA-03 Assumption IDs unique and required values numeric", True,
               f"Discount rate={rate:.4%}; horizon={horizon}; base oil price=${base_price:.2f}/bbl")
    except Exception as exc:
        record("QA-03 Assumption IDs unique and required values numeric", False, repr(exc))
        rate, horizon, base_price = None, None, None

    numeric_model_cols = list(required_model_cols - {"Development_Concept"})
    numeric_metric_cols = list(required_metric_cols - {"Development_Concept", "IRR_Status"})
    numeric_dcf_cols = list(required_dcf_cols - {"Development_Concept"})
    try:
        for col in numeric_model_cols:
            model[col] = pd.to_numeric(model[col], errors="raise")
        for col in numeric_metric_cols:
            metrics[col] = pd.to_numeric(metrics[col], errors="raise")
        for col in numeric_dcf_cols:
            dcf[col] = pd.to_numeric(dcf[col], errors="raise")
        record("QA-04 Numeric fields parse without errors", True, "All required numeric fields parsed")
    except Exception as exc:
        record("QA-04 Numeric fields parse without errors", False, repr(exc))

    concepts = sorted(model["Development_Concept"].dropna().unique().tolist())
    expected_concepts = ["Standalone_FPSO", "Subsea_Tieback"]
    record("QA-05 Expected development concepts present", concepts == expected_concepts,
           f"Found: {concepts}")
    record("QA-06 Model contains one record per concept-year", not model.duplicated(["Development_Concept", "Project_Year"]).any(),
           f"Model rows={len(model)}; duplicate concept-years={int(model.duplicated(['Development_Concept', 'Project_Year']).sum())}")
    record("QA-07 Metrics contain one record per concept", not metrics["Development_Concept"].duplicated().any()
           and sorted(metrics["Development_Concept"].tolist()) == expected_concepts,
           f"Metrics rows={len(metrics)}")
    record("QA-08 DCF has complete concept-year coverage", len(dcf) == len(expected_concepts) * horizon
           and not dcf.duplicated(["Development_Concept", "Project_Year"]).any(),
           f"DCF rows={len(dcf)}; expected={len(expected_concepts) * horizon}")

    # Missing/non-finite values and invalid annual records.
    all_finite = (np.isfinite(model[numeric_model_cols].to_numpy(dtype=float)).all()
                  and np.isfinite(metrics[[c for c in numeric_metric_cols if c != "IRR"]].to_numpy(dtype=float)).all()
                  and np.isfinite(dcf[numeric_dcf_cols].to_numpy(dtype=float)).all())
    record("QA-09 Core numeric outputs are finite", all_finite, "IRR may be NaN only when its status explains no unique root")
    valid_years = True
    for concept, group in model.groupby("Development_Concept"):
        ordered_years = sorted(group["Project_Year"].astype(int).tolist())
        valid_years = valid_years and ordered_years == list(range(1, horizon + 1))
    record("QA-10 Each concept has complete evaluation horizon", valid_years,
           f"Expected project years 1 through {horizon}")

    metric_lookup = metrics.set_index("Development_Concept", drop=False)
    dcf_lookup = dcf.set_index(["Development_Concept", "Project_Year"], drop=False)
    all_npv_ok = all_irr_ok = all_payback_ok = all_breakeven_ok = True
    all_dcf_ok = all_totals_ok = all_assumptions_ok = True
    detail_lines = []

    for concept in expected_concepts:
        group = model[model["Development_Concept"] == concept].sort_values("Project_Year").copy()
        if concept not in metric_lookup.index:
            all_npv_ok = all_irr_ok = all_payback_ok = all_breakeven_ok = False
            continue
        m = metric_lookup.loc[concept]
        years = group["Project_Year"].to_numpy(dtype=int)
        cash_flows = group["Net_Project_Cash_Flow_USD"].to_numpy(dtype=float)
        expected_discount_factors = 1.0 / (1.0 + rate) ** years
        expected_discounted = cash_flows * expected_discount_factors
        expected_cum_discounted = np.cumsum(expected_discounted)
        expected_cum_undiscounted = np.cumsum(cash_flows)

        independent_npv = float(expected_discounted.sum())
        all_npv_ok &= near(m["NPV_USD"], independent_npv)

        concept_dcf = dcf[dcf["Development_Concept"] == concept].sort_values("Project_Year")
        dcf_ok = len(concept_dcf) == horizon
        if dcf_ok:
            dcf_ok &= np.allclose(concept_dcf["Net_Project_Cash_Flow_USD"], cash_flows, atol=TOL_USD, rtol=1e-9)
            dcf_ok &= np.allclose(concept_dcf["Discount_Rate"], rate, atol=1e-12, rtol=0)
            dcf_ok &= np.allclose(concept_dcf["Discount_Factor"], expected_discount_factors, atol=1e-10, rtol=1e-9)
            dcf_ok &= np.allclose(concept_dcf["Discounted_Cash_Flow_USD"], expected_discounted, atol=TOL_USD, rtol=1e-9)
            dcf_ok &= np.allclose(concept_dcf["Cumulative_Discounted_Cash_Flow_USD"], expected_cum_discounted, atol=TOL_USD, rtol=1e-9)
            dcf_ok &= np.allclose(concept_dcf["Cumulative_Undiscounted_Cash_Flow_USD"], expected_cum_undiscounted, atol=TOL_USD, rtol=1e-9)
        all_dcf_ok &= bool(dcf_ok)

        total_checks = {
            "Total_Production_bbl": group["Annual_Oil_Production_bbl"].sum(),
            "Total_Revenue_USD": group["Revenue_USD"].sum(),
            "Total_CAPEX_USD": group["CAPEX_USD"].sum(),
            "Total_OPEX_USD": group["Total_OPEX_USD"].sum(),
            "Total_Abandonment_USD": group["Abandonment_USD"].sum(),
            "Undiscounted_Net_Cash_Flow_USD": cash_flows.sum(),
        }
        concept_totals_ok = all(near(m[col], val) for col, val in total_checks.items())
        all_totals_ok &= concept_totals_ok

        assumption_ok = near(m["Discount_Rate"], rate, atol=1e-12, rtol=0) \
            and int(m["Evaluation_Horizon_Years"]) == horizon \
            and near(m["Oil_Price_USD_per_bbl"], base_price, atol=TOL_PRICE, rtol=0) \
            and np.allclose(group["Oil_Price_USD_per_bbl"].to_numpy(dtype=float), base_price, atol=TOL_PRICE, rtol=0)
        all_assumptions_ok &= bool(assumption_ok)

        irr = m["IRR"]
        irr_status = str(m["IRR_Status"])
        if pd.notna(irr):
            irr_ok = math.isfinite(float(irr)) and float(irr) > -1.0 and abs(calculate_npv(float(irr), cash_flows)) <= 100.0
            irr_ok &= "single" in irr_status.lower()
        else:
            # A blank IRR is acceptable only when the status explicitly explains why no unique root was returned.
            irr_ok = ("multiple" in irr_status.lower() or "no irr" in irr_status.lower() or "no root" in irr_status.lower())
        all_irr_ok &= bool(irr_ok)

        expected_undisc_payback = calculate_payback(cash_flows)
        expected_disc_payback = calculate_payback(cash_flows, rate)
        def payback_matches(actual, expected):
            if expected is None:
                return pd.isna(actual)
            return pd.notna(actual) and near(actual, expected, atol=TOL_YEAR, rtol=0)
        payback_ok = payback_matches(m["Undiscounted_Payback_Year"], expected_undisc_payback)
        payback_ok &= payback_matches(m["Discounted_Payback_Year"], expected_disc_payback)
        all_payback_ok &= bool(payback_ok)

        breakeven = calculate_breakeven_price(group, rate)
        breakeven_ok = pd.notna(m["Breakeven_Oil_Price_USD_per_bbl"]) and near(
            m["Breakeven_Oil_Price_USD_per_bbl"], breakeven, atol=TOL_PRICE, rtol=1e-9
        )
        if breakeven is not None:
            costs = (group["CAPEX_USD"].to_numpy(dtype=float)
                     + group["Total_OPEX_USD"].to_numpy(dtype=float)
                     + group["Abandonment_USD"].to_numpy(dtype=float))
            breakeven_cashflows = breakeven * group["Annual_Oil_Production_bbl"].to_numpy(dtype=float) - costs
            breakeven_ok &= abs(calculate_npv(rate, breakeven_cashflows)) <= 100.0
        all_breakeven_ok &= bool(breakeven_ok)

        detail_lines.append(
            f"{concept}: NPV=${independent_npv:,.2f}; IRR="
            f"{float(irr):.6%}" if pd.notna(irr) else f"{concept}: NPV=${independent_npv:,.2f}; IRR=not reported"
        )
        detail_lines.append(
            f"  Payback={expected_undisc_payback:.4f} yr; discounted={expected_disc_payback:.4f} yr; "
            f"breakeven=${breakeven:.4f}/bbl"
        )

    record("QA-11 NPV independently reconciles to annual cash flows", all_npv_ok, "NPV = sum(CF_t / (1+r)^t)")
    record("QA-12 DCF rows reconcile independently", all_dcf_ok, "Cash flows, factors, discounted flows, and cumulative values")
    record("QA-13 Reported IRR has near-zero NPV", all_irr_ok, "IRR roots tested against independently discounted cash flows")
    record("QA-14 Undiscounted and discounted payback reconcile", all_payback_ok, "Independent cumulative-flow crossing calculation")
    record("QA-15 Breakeven oil price reconciles", all_breakeven_ok, "Recomputed price and NPV at that price")
    record("QA-16 Reported economic totals reconcile", all_totals_ok, "Production, revenue, CAPEX, OPEX, abandonment, net cash flow")
    record("QA-17 Discount rate, oil price, and horizon match assumptions", all_assumptions_ok,
           f"Expected rate={rate}; base price={base_price}; horizon={horizon}")

    print("\nIndependent results:")
    for line in detail_lines:
        print(line)

    print("\nQA results:")
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'} | {name} | {detail}")

    passed_count = sum(1 for _, passed, _ in checks if passed)
    failed_count = sum(1 for _, passed, _ in checks if not passed)
    print("\n" + "=" * 78)
    print(f"SUMMARY: {passed_count} PASSED | {failed_count} FAILED | {len(checks)} TOTAL")
    print("=" * 78)
    if failed_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
