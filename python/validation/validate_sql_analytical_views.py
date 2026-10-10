"""Validate Project 3 analytical views against their source tables.
Run from project root: py python/validation/validate_sql_analytical_views.py
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
import math
ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "offshore_field_development_economics.db"
def near(a, b, tol=0.01):
    return a is not None and b is not None and math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=tol)
def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    checks = []
    def check(name, condition, detail=""):
        checks.append((name, bool(condition), detail))
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        views = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        expected_views = {"vw_Annual_Production_Summary", "vw_Annual_Economics_Summary", "vw_Base_Investment_Comparison", "vw_Scenario_Investment_Comparison", "vw_Scenario_NPV_Comparison", "vw_Scenario_Cash_Flow_Profile"}
        check("SQLV-01 All six analytical views exist", expected_views.issubset(views), f"found={len(expected_views.intersection(views))}/6")
        if not expected_views.issubset(views):
            print_results(checks); raise SystemExit(1)
        expected_counts = {"vw_Annual_Production_Summary": 50, "vw_Annual_Economics_Summary": 50, "vw_Base_Investment_Comparison": 2, "vw_Scenario_Investment_Comparison": 6, "vw_Scenario_NPV_Comparison": 2, "vw_Scenario_Cash_Flow_Profile": 150}
        for i, (view, expected) in enumerate(expected_counts.items(), start=2):
            actual = conn.execute(f'SELECT COUNT(*) FROM "{view}"').fetchone()[0]
            check(f"SQLV-{i:02d} {view} expected row count", actual == expected, f"actual={actual}, expected={expected}")
        source = conn.execute("SELECT Development_Concept, SUM(Annual_Oil_Production_bbl) total FROM Fact_Annual_Production GROUP BY Development_Concept").fetchall()
        view = conn.execute("SELECT Development_Concept, SUM(Annual_Oil_Production_bbl) total FROM vw_Annual_Production_Summary GROUP BY Development_Concept").fetchall()
        sdict = {r["Development_Concept"]: r["total"] for r in source}; vdict = {r["Development_Concept"]: r["total"] for r in view}
        check("SQLV-08 Annual production totals reconcile", sdict.keys() == vdict.keys() and all(near(sdict[k], vdict[k]) for k in sdict), f"concepts={len(sdict)}")
        last_rows = conn.execute("""SELECT p.Development_Concept, p.Cumulative_Oil_Production_bbl FROM vw_Annual_Production_Summary p WHERE p.Project_Year=(SELECT MAX(p2.Project_Year) FROM vw_Annual_Production_Summary p2 WHERE p2.Development_Concept=p.Development_Concept)""").fetchall()
        cumulative = {r["Development_Concept"]: r["Cumulative_Oil_Production_bbl"] for r in last_rows}
        check("SQLV-09 Cumulative production equals lifetime total", cumulative.keys() == sdict.keys() and all(near(sdict[k], cumulative[k]) for k in sdict), f"concepts={len(cumulative)}")
        bsrc = conn.execute("SELECT * FROM Fact_Investment_Metrics ORDER BY 1").fetchall(); bview = conn.execute("SELECT * FROM vw_Base_Investment_Comparison ORDER BY 1").fetchall()
        check("SQLV-10 Base investment view matches source", len(bsrc) == len(bview) and [tuple(r) for r in bsrc] == [tuple(r) for r in bview], f"source={len(bsrc)}, view={len(bview)}")
        ssrc = conn.execute("SELECT * FROM Fact_Scenario_Investment_Metrics ORDER BY 1,2").fetchall(); sview = conn.execute("SELECT * FROM vw_Scenario_Investment_Comparison ORDER BY 1,2").fetchall()
        check("SQLV-11 Scenario investment view matches source", len(ssrc) == len(sview) and [tuple(r) for r in ssrc] == [tuple(r) for r in sview], f"source={len(ssrc)}, view={len(sview)}")
        mcols = {r["name"] for r in conn.execute('PRAGMA table_info("Fact_Scenario_Investment_Metrics")')}
        scenario_col = next((c for c in ("Oil_Price_Scenario", "Price_Scenario", "Scenario") if c in mcols), None)
        npv_col = next((c for c in ("NPV_USD", "NPV", "Net_Present_Value_USD") if c in mcols), None)
        concept_col = next((c for c in ("Development_Concept", "Concept") if c in mcols), None)
        pivot_cols = {r["name"] for r in conn.execute('PRAGMA table_info("vw_Scenario_NPV_Comparison")')}
        pivot_ok = {"Development_Concept", "NPV_Low_USD", "NPV_Base_USD", "NPV_High_USD"}.issubset(pivot_cols)
        pivot_rows = conn.execute("SELECT * FROM vw_Scenario_NPV_Comparison").fetchall()
        pivot_ok = pivot_ok and len(pivot_rows) == 2 and all(scenario_col and npv_col and concept_col for _ in [0])
        if pivot_ok:
            for row in pivot_rows:
                for scenario, col in (("low", "NPV_Low_USD"), ("base", "NPV_Base_USD"), ("high", "NPV_High_USD")):
                    original = conn.execute(f'SELECT "{npv_col}" FROM Fact_Scenario_Investment_Metrics WHERE "{concept_col}"=? AND lower("{scenario_col}") LIKE ?', (row["Development_Concept"], scenario + "%")).fetchone()
                    if original is None or not near(row[col], original[0]): pivot_ok = False
        check("SQLV-12 NPV pivot reconciles to six scenario metrics", pivot_ok, "two concepts × three price cases")
        scenario_econ_count = conn.execute("SELECT COUNT(*) FROM Fact_Scenario_Annual_Economics").fetchone()[0]
        joined_count = conn.execute("SELECT COUNT(*) FROM vw_Scenario_Cash_Flow_Profile").fetchone()[0]
        check("SQLV-13 Scenario cash-flow join preserves grain", scenario_econ_count == joined_count, f"economics={scenario_econ_count}, joined={joined_count}")
        duplicates = conn.execute("SELECT Development_Concept, Oil_Price_Scenario, Project_Year, COUNT(*) FROM vw_Scenario_Cash_Flow_Profile GROUP BY 1,2,3 HAVING COUNT(*)>1").fetchall()
        check("SQLV-14 Scenario cash-flow grain is unique", len(duplicates) == 0, f"duplicate_keys={len(duplicates)}")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        check("SQLV-15 SQLite integrity remains OK", integrity == "ok", integrity)
    print_results(checks)
    if any(not passed for _, passed, _ in checks): raise SystemExit(1)
def print_results(checks):
    print("=" * 78); print("PROJECT 3 — SQL ANALYTICAL VIEW VALIDATION"); print("=" * 78)
    for name, passed, detail in checks:
        print(f"{name:<58} | {'PASS' if passed else 'FAIL'}")
        if detail: print(f"  {detail}")
    print("-" * 78); print(f"Checks: {sum(p for _, p, _ in checks)}/{len(checks)} passed | Failures: {sum(not p for _, p, _ in checks)}")
if __name__ == "__main__": main()
