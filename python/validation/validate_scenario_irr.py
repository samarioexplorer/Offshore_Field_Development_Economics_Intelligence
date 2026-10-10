from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
MODEL_FILE = PROCESSED / "scenario_annual_economic_model.csv"
METRICS_FILE = PROCESSED / "scenario_investment_metrics.csv"

checks = []

# IRR roots extremely close to -100% are numerically ill-conditioned.
# These roots are retained as diagnostics but are not verified using
# ordinary floating-point NPV calculations.
IRR_ILL_CONDITIONED_THRESHOLD = -0.95
NPV_RESIDUAL_TOLERANCE_USD = 2.0

def check(name, passed, detail=""):
    passed = bool(passed)
    checks.append((name, passed))
    print(f"{'PASS' if passed else 'FAIL'} | {name}" + (f" | {detail}" if detail else ""))


def npv(rate, flows):
    years = np.arange(1, len(flows) + 1, dtype=float)
    return float(np.sum(np.asarray(flows, dtype=float) / (1.0 + rate) ** years))


def count_sign_changes(flows):
    signs = np.sign(np.asarray(flows, dtype=float))
    signs = signs[signs != 0]
    if len(signs) < 2:
        return 0
    return int(np.count_nonzero(signs[1:] != signs[:-1]))


def main():
    print("=" * 78)
    print("PROJECT 3 — INDEPENDENT SCENARIO IRR DIAGNOSTICS")
    print("=" * 78)

    for path in (MODEL_FILE, METRICS_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    model = pd.read_csv(MODEL_FILE, encoding="utf-8-sig")
    metrics = pd.read_csv(METRICS_FILE, encoding="utf-8-sig")

    required_model = {"Development_Concept", "Oil_Price_Scenario", "Project_Year", "Net_Project_Cash_Flow_USD"}
    required_metrics = {"Development_Concept", "Oil_Price_Scenario", "IRR", "IRR_Status"}
    if not required_model.issubset(model.columns):
        raise ValueError(f"Scenario model missing columns: {sorted(required_model - set(model.columns))}")
    if not required_metrics.issubset(metrics.columns):
        raise ValueError(f"Metrics file missing columns: {sorted(required_metrics - set(metrics.columns))}")

    check("IRR-01 Required scenario files and columns exist", True, "Scenario cash flows and metrics loaded")

    all_statuses_match = True
    all_reported_roots_valid = True
    all_single_roots_valid = True
    sign_pattern_consistent = True
    diagnostics = []

    for _, metric in metrics.iterrows():

        concept = metric["Development_Concept"]
        scenario = metric["Oil_Price_Scenario"]

        group = model[
            (model["Development_Concept"] == concept)
            & (model["Oil_Price_Scenario"] == scenario)
        ].sort_values("Project_Year")

        flows = pd.to_numeric(
            group["Net_Project_Cash_Flow_USD"],
            errors="raise"
        ).to_numpy(dtype=float)

        status = str(metric["IRR_Status"])
        irr = metric["IRR"]
        sign_changes = count_sign_changes(flows)

        # ---------------------------------------------------------
        # MULTIPLE IRR ROOTS
        # ---------------------------------------------------------
        if "Multiple roots found:" in status:
            roots_text = status.split("Multiple roots found:", 1)[1]

            roots = [
                float(x)
                for x in re.findall(
                    r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?",
                    roots_text
                )
            ]

            status_count_ok = len(roots) > 1 and pd.isna(irr)

            well_conditioned_roots = [
                root for root in roots
                if root > IRR_ILL_CONDITIONED_THRESHOLD
            ]

            ill_conditioned_roots = [
                root for root in roots
                if -1 < root <= IRR_ILL_CONDITIONED_THRESHOLD
            ]

            # Independently verify roots that are numerically
            # suitable for ordinary floating-point NPV evaluation.
            well_conditioned_errors = [
                abs(npv(root, flows))
                for root in well_conditioned_roots
            ]

            roots_ok = (
                len(roots) > 1
                and all(
                    np.isfinite(root) and root > -1
                    for root in roots
                )
                and len(well_conditioned_roots) > 0
                and all(
                    np.isfinite(error)
                    and error < NPV_RESIDUAL_TOLERANCE_USD
                    for error in well_conditioned_errors
                )
            )

            root_errors = []

            for root in roots:
                if root in ill_conditioned_roots:
                    root_errors.append(float("nan"))
                else:
                    root_errors.append(abs(npv(root, flows)))

            # Report numerical conditioning, but do not let this
            # informational message control the validation logic.
            if ill_conditioned_roots:
                print(
                    f"INFO | {concept} | {scenario} | "
                    f"{len(ill_conditioned_roots)} root(s) classified "
                    "as numerically ill-conditioned near -100%"
                )

            # These updates must execute for EVERY multiple-root case.
            if len(roots) > sign_changes:
                sign_pattern_consistent = False

            all_statuses_match &= status_count_ok
            all_reported_roots_valid &= roots_ok

            diagnostics.append(
                (
                    concept,
                    scenario,
                    sign_changes,
                    roots,
                    root_errors,
                    status
                )
            )

        # ---------------------------------------------------------
        # SINGLE IRR ROOT
        # ---------------------------------------------------------
        elif status == "Single numerical root found":
            status_ok = (
                pd.notna(irr)
                and np.isfinite(float(irr))
            )

            root_ok = (
                status_ok
                and float(irr) > -1
                and abs(npv(float(irr), flows))
                < NPV_RESIDUAL_TOLERANCE_USD
            )

            all_statuses_match &= status_ok
            all_single_roots_valid &= root_ok

            if sign_changes < 1:
                sign_pattern_consistent = False

            diagnostics.append(
                (
                    concept,
                    scenario,
                    sign_changes,
                    [float(irr)] if status_ok else [],
                    [
                        abs(npv(float(irr), flows))
                    ] if status_ok else [],
                    status
                )
            )

        # ---------------------------------------------------------
        # NO IDENTIFIED IRR ROOT
        # ---------------------------------------------------------
        elif status.startswith("No IRR root identified"):
            all_statuses_match &= pd.isna(irr)

            diagnostics.append(
                (
                    concept,
                    scenario,
                    sign_changes,
                    [],
                    [],
                    status
                )
            )

        # ---------------------------------------------------------
        # UNEXPECTED IRR STATUS
        # ---------------------------------------------------------
        else:
            all_statuses_match = False

            diagnostics.append(
                (
                    concept,
                    scenario,
                    sign_changes,
                    [],
                    [],
                    status
                )
            )

    check("IRR-02 IRR status agrees with reported root count", all_statuses_match,
          "Multiple roots must leave scalar IRR blank; single-root cases must report a finite IRR")
    check(
        "IRR-03 All well-conditioned reported roots independently give near-zero NPV",
        all_reported_roots_valid,
        "Roots near -100% are classified separately because ordinary "
        "floating-point NPV evaluation is unreliable there"
    )
    check("IRR-04 Each single IRR independently gives near-zero NPV", all_single_roots_valid,
          "Independent NPV residual tolerance: $2")
    check("IRR-05 Cash-flow sign changes are compatible with root counts", sign_pattern_consistent,
          "Reported distinct roots cannot exceed annual cash-flow sign changes")

    expected_multiple = {
        ("Standalone_FPSO", "Low"),
        ("Subsea_Tieback", "Low"),
    }
    actual_multiple = {
        (c, s) for c, s, _, roots, _, status in diagnostics
        if "Multiple roots found:" in status
    }
    check("IRR-06 Low-price cases explicitly identify multiple roots",
          actual_multiple == expected_multiple,
          f"Multiple-root cases: {sorted(actual_multiple)}")

    positive_roots_ok = True
    negative_roots_ok = True
    for c, s, _, roots, _, status in diagnostics:
        if (c, s) in expected_multiple:
            positive_roots_ok &= any(root > 0 for root in roots)
            negative_roots_ok &= any(-1 < root < 0 for root in roots)
    check("IRR-07 Each low-price case has a positive IRR root", positive_roots_ok,
          "Positive roots are retained in IRR_Status, not silently selected")
    check("IRR-08 Each low-price case also has a negative IRR root", negative_roots_ok,
          "Negative roots explain why a single scalar IRR is ambiguous")

    ill_conditioned_roots_ok = True

    for concept, scenario, _, roots, _, _ in diagnostics:
        if (concept, scenario) in expected_multiple:
            ill_conditioned_roots_ok &= any(
                -1 < root <= IRR_ILL_CONDITIONED_THRESHOLD
                for root in roots
            )

    check(
        "IRR-09 Near-minus-100% roots are explicitly classified as ill-conditioned",
        ill_conditioned_roots_ok,
        "Both low-price cases must retain their negative roots without "
        "claiming unreliable NPV residuals are independently verified"
    )

    print("\nRoot diagnostics:")
    for concept, scenario, sign_changes, roots, errors, status in diagnostics:
        root_labels = []

        for root, error in zip(roots, errors):
            if -1 < root <= IRR_ILL_CONDITIONED_THRESHOLD:
                label = (
                    f"{root:.6%} "
                    "(numerically ill-conditioned; NPV residual not verified)"
                )
            elif np.isfinite(error):
                label = f"{root:.6%} (|NPV|=${error:,.4f})"
            else:
                label = f"{root:.6%} (NPV residual unavailable)"

            root_labels.append(label)

        roots_display = ", ".join(root_labels) or "none reported"
        print(f"{concept} | {scenario} | sign changes={sign_changes} | roots={roots_display}")
        print(f"  Status: {status}")

    passed = sum(ok for _, ok in checks)
    failed = len(checks) - passed
    print("\n" + "=" * 78)
    print(f"SUMMARY: {passed} PASSED | {failed} FAILED | {len(checks)} TOTAL")
    print("=" * 78)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
