from __future__ import annotations

import math
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
DATABASE_DIR = ROOT / "database"
DATABASE_FILE = DATABASE_DIR / "offshore_field_development_economics.db"
TEMP_DATABASE_FILE = DATABASE_DIR / "offshore_field_development_economics.building.db"

# Source file -> SQLite table -> composite primary key
DATASETS = [
    {
        "file": "annual_production_profiles.csv",
        "table": "Fact_Annual_Production",
        "key": ["Development_Concept", "Project_Year"],
        "expected_rows": 50,
    },
    {
        "file": "annual_economic_model.csv",
        "table": "Fact_Annual_Economics",
        "key": ["Development_Concept", "Project_Year"],
        "expected_rows": 50,
    },
    {
        "file": "investment_metrics.csv",
        "table": "Fact_Investment_Metrics",
        "key": ["Development_Concept"],
        "expected_rows": 2,
    },
    {
        "file": "scenario_annual_economic_model.csv",
        "table": "Fact_Scenario_Annual_Economics",
        "key": ["Development_Concept", "Oil_Price_Scenario", "Project_Year"],
        "expected_rows": 150,
    },
    {
        "file": "scenario_discounted_cash_flow.csv",
        "table": "Fact_Scenario_Discounted_Cash_Flow",
        "key": ["Development_Concept", "Oil_Price_Scenario", "Project_Year"],
        "expected_rows": 150,
    },
    {
        "file": "scenario_investment_metrics.csv",
        "table": "Fact_Scenario_Investment_Metrics",
        "key": ["Development_Concept", "Oil_Price_Scenario"],
        "expected_rows": 6,
    },
]

REQUIRED_COLUMNS = {
    "annual_production_profiles.csv": {
        "Development_Concept", "Project_Year", "Annual_Oil_Production_bbl",
        "Assumption_Status",
    },
    "annual_economic_model.csv": {
        "Development_Concept", "Project_Year", "CAPEX_USD",
        "Revenue_USD", "Net_Project_Cash_Flow_USD", "Economic_Status",
    },
    "investment_metrics.csv": {
        "Development_Concept", "NPV_USD", "IRR", "IRR_Status",
        "Economic_Status",
    },
    "scenario_annual_economic_model.csv": {
        "Development_Concept", "Oil_Price_Scenario", "Project_Year",
        "Net_Project_Cash_Flow_USD", "Economic_Status",
    },
    "scenario_discounted_cash_flow.csv": {
        "Development_Concept", "Oil_Price_Scenario", "Project_Year",
        "Discounted_Cash_Flow_USD", "Cumulative_Discounted_Cash_Flow_USD",
    },
    "scenario_investment_metrics.csv": {
        "Development_Concept", "Oil_Price_Scenario", "NPV_USD", "IRR",
        "IRR_Status", "Economic_Status",
    },
}


def sqlite_type(series: pd.Series) -> str:
    """Map pandas column types to appropriate SQLite storage types."""
    if pd.api.types.is_bool_dtype(series.dtype):
        return "INTEGER"
    if pd.api.types.is_integer_dtype(series.dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(series.dtype):
        return "REAL"
    return "TEXT"


def sql_identifier(value: str) -> str:
    """Quote a known identifier safely for SQLite."""
    return '"' + value.replace('"', '""') + '"'


def validate_source(dataset: dict) -> pd.DataFrame:
    path = PROCESSED_DIR / dataset["file"]
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")

    missing = REQUIRED_COLUMNS[dataset["file"]] - set(df.columns)
    if missing:
        raise ValueError(
            f"{dataset['file']} is missing required columns: {sorted(missing)}"
        )

    if len(df) != dataset["expected_rows"]:
        raise ValueError(
            f"{dataset['file']} expected {dataset['expected_rows']} rows, "
            f"found {len(df)}"
        )

    if not df.columns.is_unique:
        raise ValueError(f"{dataset['file']} contains duplicate column names")

    key_columns = dataset["key"]
    null_key_rows = df[key_columns].isna().any(axis=1)
    if null_key_rows.any():
        raise ValueError(
            f"{dataset['file']} has {int(null_key_rows.sum())} rows with NULL key values"
        )

    duplicate_rows = int(df.duplicated(subset=key_columns, keep=False).sum())
    if duplicate_rows:
        raise ValueError(
            f"{dataset['file']} has duplicate key rows for {key_columns}: "
            f"{duplicate_rows} affected rows"
        )

    # Project_Year is expected to be a whole number wherever it appears.
    if "Project_Year" in df.columns:
        years = pd.to_numeric(df["Project_Year"], errors="raise")
        if not (years.dropna() % 1 == 0).all():
            raise ValueError(f"{dataset['file']} has non-integer Project_Year values")

    return df


def create_and_load_table(
    connection: sqlite3.Connection,
    dataset: dict,
    df: pd.DataFrame,
) -> int:
    table = dataset["table"]
    key_columns = dataset["key"]

    definitions = []
    for column in df.columns:
        col_type = sqlite_type(df[column])
        definition = f"{sql_identifier(column)} {col_type}"
        if column in key_columns:
            definition += " NOT NULL"
        definitions.append(definition)

    primary_key = ", ".join(sql_identifier(column) for column in key_columns)
    create_sql = (
        f"CREATE TABLE {sql_identifier(table)} "
        f"({', '.join(definitions)}, PRIMARY KEY ({primary_key}))"
    )
    connection.execute(create_sql)

    insert_columns = ", ".join(sql_identifier(column) for column in df.columns)
    placeholders = ", ".join("?" for _ in df.columns)
    insert_sql = (
        f"INSERT INTO {sql_identifier(table)} ({insert_columns}) "
        f"VALUES ({placeholders})"
    )

    # Convert pandas missing values to Python None so SQLite stores SQL NULL.
    cleaned = df.astype(object).where(pd.notna(df), None)
    records = [
        tuple(None if (isinstance(value, float) and math.isnan(value)) else value
              for value in row)
        for row in cleaned.itertuples(index=False, name=None)
    ]
    connection.executemany(insert_sql, records)

    database_count = connection.execute(
        f"SELECT COUNT(*) FROM {sql_identifier(table)}"
    ).fetchone()[0]

    if database_count != len(df):
        raise RuntimeError(
            f"{table}: source rows={len(df)}, database rows={database_count}"
        )

    return database_count


def main() -> int:
    print("=" * 78)
    print("PROJECT 3 — SQLITE DATABASE BUILD")
    print("=" * 78)

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    if TEMP_DATABASE_FILE.exists():
        TEMP_DATABASE_FILE.unlink()

    validated_sources: list[tuple[dict, pd.DataFrame]] = []
    for dataset in DATASETS:
        df = validate_source(dataset)
        validated_sources.append((dataset, df))
        print(
            f"PASS | Source validation | {dataset['file']} | "
            f"{len(df)} rows | key={dataset['key']}"
        )

    total_loaded = 0
    try:
        with closing(sqlite3.connect(TEMP_DATABASE_FILE)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute("BEGIN")

            for dataset, df in validated_sources:
                loaded = create_and_load_table(connection, dataset, df)
                total_loaded += loaded
                print(
                    f"PASS | Loaded {dataset['table']} | "
                    f"source={len(df)} | database={loaded}"
                )

            # Record the source-file lineage and build timestamp-independent metadata.
            connection.execute(
                """
                CREATE TABLE Database_Metadata (
                    Metadata_Key TEXT PRIMARY KEY,
                    Metadata_Value TEXT NOT NULL
                )
                """
            )
            metadata = [
                ("Project_Name", "Offshore_Field_Development_Economics_Intelligence"),
                ("Build_Method", "Python CSV-to-SQLite loader"),
                ("Source_Directory", "data/processed"),
                ("Expected_Total_Data_Rows", str(sum(d["expected_rows"] for d in DATASETS))),
                ("Economic_Assumption_Status", "Proposed_Illustrative"),
            ]
            connection.executemany(
                "INSERT INTO Database_Metadata (Metadata_Key, Metadata_Value) VALUES (?, ?)",
                metadata,
            )

            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"SQLite integrity check failed: {integrity}")

            connection.commit()

        expected_total = sum(d["expected_rows"] for d in DATASETS)
        if total_loaded != expected_total:
            raise RuntimeError(
                f"Total row mismatch: expected {expected_total}, loaded {total_loaded}"
            )

        # Replace the final database only after the temporary build succeeds.
        TEMP_DATABASE_FILE.replace(DATABASE_FILE)

    except Exception:
        if TEMP_DATABASE_FILE.exists():
            TEMP_DATABASE_FILE.unlink()
        raise

    print("-" * 78)
    print("PASS | SQLite integrity_check | ok")
    print(f"PASS | Total analytical rows loaded | {total_loaded}/{total_loaded}")
    print(f"PASS | Database created | {DATABASE_FILE}")
    print("NOTE | Database contains illustrative model outputs, not field forecasts.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL | Database build | {exc}", file=sys.stderr)
        raise SystemExit(1)
