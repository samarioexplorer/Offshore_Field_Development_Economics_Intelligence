"""Create version-controlled SQLite analytical views for Project 3.

Run from the project root:
    py python/preparation/create_sql_analytical_views.py

This introspects the SQLite schema, generates sql/02_analytical_views.sql,
applies the views, and prints their row counts. The database stays local.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "offshore_field_development_economics.db"
SQL_PATH = ROOT / "sql" / "02_analytical_views.sql"
TABLES = {
    "production": "Fact_Annual_Production",
    "economics": "Fact_Annual_Economics",
    "base_metrics": "Fact_Investment_Metrics",
    "scenario_economics": "Fact_Scenario_Annual_Economics",
    "scenario_dcf": "Fact_Scenario_Discounted_Cash_Flow",
    "scenario_metrics": "Fact_Scenario_Investment_Metrics",
}

def columns(conn, table):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    if not rows:
        raise RuntimeError(f"Required table missing or has no columns: {table}")
    return [row[1] for row in rows]

def resolve(existing, candidates, label):
    lookup = {c.lower(): c for c in existing}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    raise RuntimeError(f"Could not resolve {label}. Available columns: {', '.join(existing)}. Accepted names: {', '.join(candidates)}")

def q(identifier):
    return '"' + identifier.replace('"', '""') + '"'

def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        table_names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in TABLES.values():
            if table not in table_names:
                raise RuntimeError(f"Required table is missing: {table}")
        pcols = columns(conn, TABLES["production"])
        ecols = columns(conn, TABLES["economics"])
        bcols = columns(conn, TABLES["base_metrics"])
        secols = columns(conn, TABLES["scenario_economics"])
        sdcols = columns(conn, TABLES["scenario_dcf"])
        smcols = columns(conn, TABLES["scenario_metrics"])

        p_concept = resolve(pcols, ["Development_Concept", "Concept"], "production concept")
        p_year = resolve(pcols, ["Project_Year", "Year"], "production year")
        p_oil = resolve(pcols, ["Annual_Oil_Production_bbl", "Annual_Production_bbl", "Oil_Production_bbl", "Annual_Oil_bbl"], "annual oil production")
        e_concept = resolve(ecols, ["Development_Concept", "Concept"], "economics concept")
        e_year = resolve(ecols, ["Project_Year", "Year"], "economics year")
        b_concept = resolve(bcols, ["Development_Concept", "Concept"], "base metrics concept")
        sm_concept = resolve(smcols, ["Development_Concept", "Concept"], "scenario metrics concept")
        sm_scenario = resolve(smcols, ["Oil_Price_Scenario", "Price_Scenario", "Scenario"], "scenario metrics scenario")
        se_concept = resolve(secols, ["Development_Concept", "Concept"], "scenario economics concept")
        se_scenario = resolve(secols, ["Oil_Price_Scenario", "Price_Scenario", "Scenario"], "scenario economics scenario")
        se_year = resolve(secols, ["Project_Year", "Year"], "scenario economics year")
        sd_concept = resolve(sdcols, ["Development_Concept", "Concept"], "scenario DCF concept")
        sd_scenario = resolve(sdcols, ["Oil_Price_Scenario", "Price_Scenario", "Scenario"], "scenario DCF scenario")
        sd_year = resolve(sdcols, ["Project_Year", "Year"], "scenario DCF year")
        b_npv = resolve(bcols, ["NPV_USD", "NPV", "Net_Present_Value_USD"], "base NPV")
        sm_npv = resolve(smcols, ["NPV_USD", "NPV", "Net_Present_Value_USD"], "scenario NPV")
        e_cash = resolve(
                            ecols,
                            [
                                "Net_Project_Cash_Flow_USD",
                                "Net_Cash_Flow_USD",
                                "Annual_Net_Cash_Flow_USD",
                                "Net_Cash_Flow",
                            ],
                            "annual net cash flow",
                        )
        se_cash = resolve(
                                secols,
                                [
                                    "Net_Project_Cash_Flow_USD",
                                    "Net_Cash_Flow_USD",
                                    "Annual_Net_Cash_Flow_USD",
                                    "Net_Cash_Flow",
                                ],
                                "scenario net cash flow",
                            )
        sd_dcf = resolve(sdcols, ["Discounted_Cash_Flow_USD", "Discounted_Net_Cash_Flow_USD", "Discounted_Cash_Flow"], "discounted cash flow")
        duplicate = conn.execute(f'''SELECT {q(se_concept)}, {q(se_scenario)}, {q(se_year)}, COUNT(*)
            FROM {q(TABLES['scenario_economics'])} GROUP BY 1,2,3 HAVING COUNT(*) > 1 LIMIT 1''').fetchone()
        if duplicate:
            raise RuntimeError(f"Scenario economics grain is not unique: {duplicate}")

        sql = f'''-- Project 3 — version-controlled analytical views
-- Generated by python/preparation/create_sql_analytical_views.py.
-- Source SQLite database is local/generated and is not committed to Git.

DROP VIEW IF EXISTS vw_Annual_Production_Summary;
DROP VIEW IF EXISTS vw_Annual_Economics_Summary;
DROP VIEW IF EXISTS vw_Base_Investment_Comparison;
DROP VIEW IF EXISTS vw_Scenario_Investment_Comparison;
DROP VIEW IF EXISTS vw_Scenario_NPV_Comparison;
DROP VIEW IF EXISTS vw_Scenario_Cash_Flow_Profile;

CREATE VIEW vw_Annual_Production_Summary AS
SELECT {q(p_concept)} AS Development_Concept,
       {q(p_year)} AS Project_Year,
       {q(p_oil)} AS Annual_Oil_Production_bbl,
       SUM({q(p_oil)}) OVER (PARTITION BY {q(p_concept)} ORDER BY {q(p_year)}
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS Cumulative_Oil_Production_bbl
FROM {q(TABLES['production'])};

CREATE VIEW vw_Annual_Economics_Summary AS SELECT * FROM {q(TABLES['economics'])};
CREATE VIEW vw_Base_Investment_Comparison AS SELECT * FROM {q(TABLES['base_metrics'])};
CREATE VIEW vw_Scenario_Investment_Comparison AS SELECT * FROM {q(TABLES['scenario_metrics'])};

CREATE VIEW vw_Scenario_NPV_Comparison AS
SELECT {q(sm_concept)} AS Development_Concept,
       MAX(CASE WHEN lower({q(sm_scenario)}) IN ('low','low price') THEN {q(sm_npv)} END) AS NPV_Low_USD,
       MAX(CASE WHEN lower({q(sm_scenario)}) IN ('base','base price') THEN {q(sm_npv)} END) AS NPV_Base_USD,
       MAX(CASE WHEN lower({q(sm_scenario)}) IN ('high','high price') THEN {q(sm_npv)} END) AS NPV_High_USD,
       MAX(CASE WHEN lower({q(sm_scenario)}) IN ('low','low price') THEN {q(sm_npv)} END)
         - MAX(CASE WHEN lower({q(sm_scenario)}) IN ('base','base price') THEN {q(sm_npv)} END) AS NPV_Low_vs_Base_USD,
       MAX(CASE WHEN lower({q(sm_scenario)}) IN ('high','high price') THEN {q(sm_npv)} END)
         - MAX(CASE WHEN lower({q(sm_scenario)}) IN ('base','base price') THEN {q(sm_npv)} END) AS NPV_High_vs_Base_USD
FROM {q(TABLES['scenario_metrics'])} GROUP BY {q(sm_concept)};

CREATE VIEW vw_Scenario_Cash_Flow_Profile AS
SELECT se.{q(se_concept)} AS Development_Concept,
       se.{q(se_scenario)} AS Oil_Price_Scenario,
       se.{q(se_year)} AS Project_Year,
       se.{q(se_cash)} AS Net_Cash_Flow_USD,
       sd.{q(sd_dcf)} AS Discounted_Cash_Flow_USD
FROM {q(TABLES['scenario_economics'])} se
INNER JOIN {q(TABLES['scenario_dcf'])} sd
 ON se.{q(se_concept)} = sd.{q(sd_concept)}
AND se.{q(se_scenario)} = sd.{q(sd_scenario)}
AND se.{q(se_year)} = sd.{q(sd_year)};
'''
        SQL_PATH.parent.mkdir(parents=True, exist_ok=True)
        SQL_PATH.write_text(sql, encoding="utf-8")
        conn.executescript(sql)
        conn.commit()
        print("=" * 72)
        print("PROJECT 3 — SQL ANALYTICAL VIEWS")
        print("=" * 72)
        print(f"SQL saved: {SQL_PATH.relative_to(ROOT)}")
        for view in ["vw_Annual_Production_Summary", "vw_Annual_Economics_Summary", "vw_Base_Investment_Comparison", "vw_Scenario_Investment_Comparison", "vw_Scenario_NPV_Comparison", "vw_Scenario_Cash_Flow_Profile"]:
            count = conn.execute(f'SELECT COUNT(*) FROM "{view}"').fetchone()[0]
            print(f"{view:<40} {count:>6} rows")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"SQLite integrity_check: {integrity}")
        if integrity != "ok":
            raise RuntimeError("SQLite integrity check failed")
        print("\nViews created successfully.")

if __name__ == "__main__":
    main()
