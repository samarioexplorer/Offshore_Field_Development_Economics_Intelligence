from pathlib import Path
import sqlite3
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATABASE_FILE = (
    ROOT / "database" / "offshore_field_development_economics.db"
)

PROCESSED = ROOT / "data" / "processed"

checks = []

# Financial totals are compared with a small absolute tolerance.
USD_TOLERANCE = 2.0
VOLUME_TOLERANCE_BBL = 0.01


def check(name, passed, detail=""):
    passed = bool(passed)
    checks.append((name, passed))

    label = "PASS" if passed else "FAIL"

    print(
        f"{label} | {name}"
        + (f" | {detail}" if detail else "")
    )


def read_csv(filename):
    path = PROCESSED / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required CSV not found: {path}"
        )

    return pd.read_csv(path, encoding="utf-8-sig")


def read_sql(connection, query):
    return pd.read_sql_query(query, connection)


def close_enough(actual, expected, tolerance):
    return (
        np.isfinite(actual)
        and np.isfinite(expected)
        and abs(float(actual) - float(expected)) <= tolerance
    )


def main():
    print("=" * 78)
    print("PROJECT 3 — INDEPENDENT SQLITE RECONCILIATION")
    print("=" * 78)

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    production_csv = read_csv(
        "annual_production_profiles.csv"
    )

    economics_csv = read_csv(
        "annual_economic_model.csv"
    )

    metrics_csv = read_csv(
        "investment_metrics.csv"
    )

    scenario_economics_csv = read_csv(
        "scenario_annual_economic_model.csv"
    )

    scenario_dcf_csv = read_csv(
        "scenario_discounted_cash_flow.csv"
    )

    scenario_metrics_csv = read_csv(
        "scenario_investment_metrics.csv"
    )

    with sqlite3.connect(DATABASE_FILE) as connection:

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        check(
            "SQL-01 SQLite database integrity",
            integrity == "ok",
            f"integrity_check={integrity}"
        )

        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        expected_tables = {
            "Database_Metadata",
            "Fact_Annual_Production",
            "Fact_Annual_Economics",
            "Fact_Investment_Metrics",
            "Fact_Scenario_Annual_Economics",
            "Fact_Scenario_Discounted_Cash_Flow",
            "Fact_Scenario_Investment_Metrics",
        }

        check(
            "SQL-02 Expected tables exist",
            expected_tables.issubset(tables),
            f"Missing tables: {sorted(expected_tables - tables)}"
        )

        table_sources = [
            (
                "Fact_Annual_Production",
                production_csv
            ),
            (
                "Fact_Annual_Economics",
                economics_csv
            ),
            (
                "Fact_Investment_Metrics",
                metrics_csv
            ),
            (
                "Fact_Scenario_Annual_Economics",
                scenario_economics_csv
            ),
            (
                "Fact_Scenario_Discounted_Cash_Flow",
                scenario_dcf_csv
            ),
            (
                "Fact_Scenario_Investment_Metrics",
                scenario_metrics_csv
            ),
        ]

        row_counts_ok = True
        row_count_details = []

        for table, source_df in table_sources:
            sql_count = connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]

            matched = sql_count == len(source_df)

            row_counts_ok &= matched

            row_count_details.append(
                f"{table}={sql_count}/{len(source_df)}"
            )

        check(
            "SQL-03 Database row counts reconcile to CSV",
            row_counts_ok,
            "; ".join(row_count_details)
        )

        # ---------------------------------------------------------
        # Production reconciliation
        # ---------------------------------------------------------

        production_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                COUNT(*) AS Record_Count,
                SUM(Annual_Oil_Production_bbl)
                    AS Total_Production_bbl
            FROM Fact_Annual_Production
            GROUP BY Development_Concept
            ORDER BY Development_Concept
            """
        )

        production_source = (
            production_csv
            .groupby("Development_Concept")
            .agg(
                Record_Count=("Project_Year", "size"),
                Total_Production_bbl=(
                    "Annual_Oil_Production_bbl",
                    "sum"
                ),
            )
            .reset_index()
        )

        production_compare = production_source.merge(
            production_sql,
            on="Development_Concept",
            suffixes=("_CSV", "_SQL"),
            validate="one_to_one"
        )

        production_ok = (
            len(production_compare) == 2
            and (
                production_compare["Record_Count_CSV"]
                == production_compare["Record_Count_SQL"]
            ).all()
            and all(
                close_enough(sql_value, csv_value, VOLUME_TOLERANCE_BBL)
                for sql_value, csv_value in zip(
                    production_compare["Total_Production_bbl_SQL"],
                    production_compare["Total_Production_bbl_CSV"]
                )
            )
        )

        check(
            "SQL-04 Annual production reconciles by concept",
            production_ok,
            "SQL totals compared with annual production CSV"
        )

        # ---------------------------------------------------------
        # Base economic totals
        # ---------------------------------------------------------

        economics_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                COUNT(*) AS Record_Count,
                SUM(Annual_Oil_Production_bbl) AS Total_Production_bbl,
                SUM(Revenue_USD) AS Total_Revenue_USD,
                SUM(CAPEX_USD) AS Total_CAPEX_USD,
                SUM(Total_OPEX_USD) AS Total_OPEX_USD,
                SUM(Abandonment_USD) AS Total_Abandonment_USD,
                SUM(Net_Project_Cash_Flow_USD)
                    AS Undiscounted_Net_Cash_Flow_USD
            FROM Fact_Annual_Economics
            GROUP BY Development_Concept
            ORDER BY Development_Concept
            """
        )

        base_columns = [
            "Total_Production_bbl",
            "Total_Revenue_USD",
            "Total_CAPEX_USD",
            "Total_OPEX_USD",
            "Total_Abandonment_USD",
            "Undiscounted_Net_Cash_Flow_USD",
        ]

        economics_compare = metrics_csv.merge(
            economics_sql,
            on="Development_Concept",
            suffixes=("_CSV", "_SQL"),
            validate="one_to_one"
        )

        economics_ok = len(economics_compare) == 2

        for column in base_columns:
            tolerance = (
                VOLUME_TOLERANCE_BBL
                if column == "Total_Production_bbl"
                else USD_TOLERANCE
            )

            csv_values = economics_compare[
                f"{column}_CSV"
            ]

            sql_values = economics_compare[
                f"{column}_SQL"
            ]

            economics_ok &= all(
                close_enough(sql_value, csv_value, tolerance)
                for sql_value, csv_value in zip(
                    sql_values,
                    csv_values
                )
            )

        check(
            "SQL-05 Base economic totals reconcile",
            economics_ok,
            "Production, revenue, CAPEX, OPEX, abandonment and cash flow"
        )

        # ---------------------------------------------------------
        # NPV reconciliation using the documented convention:
        # Year 1 cash flow is discounted by one period.
        # ---------------------------------------------------------

        npv_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                SUM(
                    Net_Project_Cash_Flow_USD
                    / POWER(
                        1.0 + Discount_Rate,
                        Project_Year
                    )
                ) AS Recalculated_NPV_USD
            FROM (
                SELECT
                    e.Development_Concept,
                    e.Project_Year,
                    e.Net_Project_Cash_Flow_USD,
                    m.Discount_Rate
                FROM Fact_Annual_Economics e
                JOIN Fact_Investment_Metrics m
                    ON e.Development_Concept =
                       m.Development_Concept
            )
            GROUP BY Development_Concept
            ORDER BY Development_Concept
            """
        )

        npv_compare = metrics_csv[
            ["Development_Concept", "NPV_USD"]
        ].merge(
            npv_sql,
            on="Development_Concept",
            validate="one_to_one"
        )

        npv_ok = len(npv_compare) == 2 and all(
            close_enough(sql_value, csv_value, USD_TOLERANCE)
            for sql_value, csv_value in zip(
                npv_compare["Recalculated_NPV_USD"],
                npv_compare["NPV_USD"]
            )
        )

        check(
            "SQL-06 Base-case NPV independently recalculates",
            npv_ok,
            "Year 1 discounted by one period; source discount rate"
        )

        # ---------------------------------------------------------
        # Scenario annual cash flow reconciliation
        # ---------------------------------------------------------

        scenario_annual_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                Oil_Price_Scenario,
                Project_Year,
                Net_Project_Cash_Flow_USD
            FROM Fact_Scenario_Annual_Economics
            ORDER BY
                Development_Concept,
                Oil_Price_Scenario,
                Project_Year
            """
        )

        scenario_annual_compare = scenario_economics_csv[
            [
                "Development_Concept",
                "Oil_Price_Scenario",
                "Project_Year",
                "Net_Project_Cash_Flow_USD",
            ]
        ].merge(
            scenario_annual_sql,
            on=[
                "Development_Concept",
                "Oil_Price_Scenario",
                "Project_Year",
            ],
            suffixes=("_CSV", "_SQL"),
            validate="one_to_one"
        )

        scenario_annual_ok = (
            len(scenario_annual_compare)
            == len(scenario_economics_csv)
            and all(
                close_enough(sql_value, csv_value, USD_TOLERANCE)
                for sql_value, csv_value in zip(
                    scenario_annual_compare[
                        "Net_Project_Cash_Flow_USD_SQL"
                    ],
                    scenario_annual_compare[
                        "Net_Project_Cash_Flow_USD_CSV"
                    ]
                )
            )
        )

        check(
            "SQL-07 Scenario annual cash flows reconcile",
            scenario_annual_ok,
            "All concept-scenario-year records compared"
        )

        # ---------------------------------------------------------
        # Scenario NPV reconciliation
        # ---------------------------------------------------------

        scenario_npv_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                Oil_Price_Scenario,
                SUM(
                    Net_Project_Cash_Flow_USD
                    / POWER(1.0 + Discount_Rate, Project_Year)
                ) AS Recalculated_NPV_USD
            FROM Fact_Scenario_Discounted_Cash_Flow
            GROUP BY
                Development_Concept,
                Oil_Price_Scenario
            ORDER BY
                Development_Concept,
                Oil_Price_Scenario
            """
        )

        scenario_npv_compare = scenario_metrics_csv[
            [
                "Development_Concept",
                "Oil_Price_Scenario",
                "NPV_USD",
            ]
        ].merge(
            scenario_npv_sql,
            on=[
                "Development_Concept",
                "Oil_Price_Scenario",
            ],
            validate="one_to_one"
        )

        scenario_npv_ok = (
            len(scenario_npv_compare) == 6
            and all(
                close_enough(sql_value, csv_value, USD_TOLERANCE)
                for sql_value, csv_value in zip(
                    scenario_npv_compare["Recalculated_NPV_USD"],
                    scenario_npv_compare["NPV_USD"]
                )
            )
        )

        check(
            "SQL-08 Scenario NPV independently recalculates",
            scenario_npv_ok,
            "Six concept-scenario combinations; source discount rate"
        )

        # ---------------------------------------------------------
        # Discounted cash-flow schedule reconciliation
        # ---------------------------------------------------------

        dcf_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                Oil_Price_Scenario,
                Project_Year,
                Net_Project_Cash_Flow_USD,
                Discount_Rate,
                Discount_Factor,
                Discounted_Cash_Flow_USD,
                Cumulative_Discounted_Cash_Flow_USD,
                Cumulative_Undiscounted_Cash_Flow_USD
            FROM Fact_Scenario_Discounted_Cash_Flow
            ORDER BY
                Development_Concept,
                Oil_Price_Scenario,
                Project_Year
            """
        )

        dcf_compare = scenario_dcf_csv.merge(
            dcf_sql,
            on=[
                "Development_Concept",
                "Oil_Price_Scenario",
                "Project_Year",
            ],
            suffixes=("_CSV", "_SQL"),
            validate="one_to_one"
        )

        dcf_numeric_columns = [
            "Net_Project_Cash_Flow_USD",
            "Discount_Rate",
            "Discount_Factor",
            "Discounted_Cash_Flow_USD",
            "Cumulative_Discounted_Cash_Flow_USD",
            "Cumulative_Undiscounted_Cash_Flow_USD",
        ]

        dcf_ok = len(dcf_compare) == len(scenario_dcf_csv)

        for column in dcf_numeric_columns:
            tolerance = (
                1e-12
                if column in ["Discount_Rate", "Discount_Factor"]
                else USD_TOLERANCE
            )

            dcf_ok &= all(
                close_enough(sql_value, csv_value, tolerance)
                for sql_value, csv_value in zip(
                    dcf_compare[f"{column}_SQL"],
                    dcf_compare[f"{column}_CSV"]
                )
            )

        check(
            "SQL-09 Discounted cash-flow records reconcile",
            dcf_ok,
            "Annual and cumulative discounted/undiscounted cash flows"
        )

        # ---------------------------------------------------------
        # Scenario metric coverage and status preservation
        # ---------------------------------------------------------

        scenario_metrics_sql = read_sql(
            connection,
            """
            SELECT
                Development_Concept,
                Oil_Price_Scenario,
                NPV_USD,
                IRR,
                IRR_Status,
                Economic_Status
            FROM Fact_Scenario_Investment_Metrics
            ORDER BY
                Development_Concept,
                Oil_Price_Scenario
            """
        )

        scenario_metrics_compare = scenario_metrics_csv.merge(
            scenario_metrics_sql,
            on=[
                "Development_Concept",
                "Oil_Price_Scenario",
            ],
            suffixes=("_CSV", "_SQL"),
            validate="one_to_one"
        )

        metric_values_ok = (
            len(scenario_metrics_compare) == 6
            and all(
                close_enough(sql_value, csv_value, USD_TOLERANCE)
                for sql_value, csv_value in zip(
                    scenario_metrics_compare["NPV_USD_SQL"],
                    scenario_metrics_compare["NPV_USD_CSV"]
                )
            )
            and scenario_metrics_compare["IRR_Status_SQL"].equals(
                scenario_metrics_compare["IRR_Status_CSV"]
            )
            and scenario_metrics_compare["Economic_Status_SQL"].equals(
                scenario_metrics_compare["Economic_Status_CSV"]
            )
        )

        # pandas treats NULL scalar IRR values as NaN; compare null masks
        # before comparing finite values.
        sql_irr = scenario_metrics_compare["IRR_SQL"]
        csv_irr = scenario_metrics_compare["IRR_CSV"]

        irr_nulls_match = sql_irr.isna().equals(csv_irr.isna())

        finite_mask = sql_irr.notna() & csv_irr.notna()

        irr_values_match = all(
            close_enough(sql_value, csv_value, 1e-10)
            for sql_value, csv_value in zip(
                sql_irr[finite_mask],
                csv_irr[finite_mask]
            )
        )

        metric_values_ok &= irr_nulls_match and irr_values_match

        check(
            "SQL-10 Scenario investment metrics and status reconcile",
            metric_values_ok,
            "NPV, IRR values/NULLs, IRR status and economic status"
        )

    passed = sum(ok for _, ok in checks)
    failed = len(checks) - passed

    print("\n" + "=" * 78)
    print(
        f"SUMMARY: {passed} PASSED | {failed} FAILED | "
        f"{len(checks)} TOTAL"
    )
    print("=" * 78)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR | SQL reconciliation | {exc}", file=sys.stderr)
        raise SystemExit(1)