
"""
Offshore Field Development Economics Intelligence
End-to-end reproducible pipeline orchestrator.

Run from the project root:
    py python/run_pipeline.py

The pipeline executes existing scripts in dependency order and stops
immediately when any step fails.
"""

from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


PIPELINE_STEPS = [
    (
        "Validate assumptions",
        "python/validation/validate_assumptions.py",
    ),
    (
        "Generate production profiles",
        "python/generation/generate_production_profiles.py",
    ),
    (
        "Validate production profiles",
        "python/validation/validate_production_profiles.py",
    ),
    (
        "Build annual economic model",
        "python/analytics/build_annual_economic_model.py",
    ),
    (
        "Validate annual economic model",
        "python/validation/validate_annual_economic_model.py",
    ),
    (
        "Calculate investment metrics and discounted cash flows",
        "python/analytics/calculate_investment_metrics.py",
    ),
    (
        "Validate investment metrics",
        "python/validation/validate_investment_metrics.py",
    ),
    (
        "Generate oil-price scenarios",
        "python/analytics/build_oil_price_scenarios.py",
    ),
    (
        "Validate oil-price scenarios",
        "python/validation/validate_oil_price_scenarios.py",
    ),
    (
        "Validate scenario IRR calculations",
        "python/validation/validate_scenario_irr.py",
    ),
    (
        "Build SQLite database",
        "python/preparation/build_sqlite_database.py",
    ),
    (
        "Create SQL analytical views",
        "python/preparation/create_sql_analytical_views.py",
    ),
    (
        "Validate SQL analytical views",
        "python/validation/validate_sql_analytical_views.py",
    ),
    (
        "Validate SQL reconciliation",
        "python/validation/validate_sql_reconciliation.py",
    ),
]


def run_step(number: int, total: int, title: str, relative_script: str) -> bool:
    """Execute one project script and report its result."""

    script_path = ROOT / relative_script

    print("\n" + "=" * 78)
    print(f"STEP {number}/{total}: {title}")
    print("=" * 78)

    if not script_path.is_file():
        print(f"ERROR: Script not found: {script_path}")
        return False

    started = time.perf_counter()

    try:
        result = subprocess.run(
            [PYTHON, str(script_path)],
            cwd=ROOT,
            check=False,
        )
    except OSError as exc:
        print(f"ERROR: Could not execute script: {exc}")
        return False

    elapsed = time.perf_counter() - started

    if result.returncode != 0:
        print(f"\nFAILED: {title}")
        print(f"Exit code: {result.returncode}")
        print("Pipeline stopped. Correct the failure before rerunning.")
        return False

    print(f"\nPASSED: {title} ({elapsed:.2f} seconds)")
    return True


def main() -> int:
    """Run the complete pipeline."""

    print("=" * 78)
    print("OFFSHORE FIELD DEVELOPMENT ECONOMICS INTELLIGENCE")
    print("REPRODUCIBLE PIPELINE")
    print("=" * 78)
    print(f"Project root: {ROOT}")
    print(f"Python executable: {PYTHON}")
    print(f"Pipeline steps: {len(PIPELINE_STEPS)}")

    pipeline_started = time.perf_counter()
    total_steps = len(PIPELINE_STEPS)

    for number, (title, relative_script) in enumerate(
        PIPELINE_STEPS,
        start=1,
    ):
        if not run_step(number, total_steps, title, relative_script):
            elapsed = time.perf_counter() - pipeline_started
            print("\n" + "=" * 78)
            print("PIPELINE FAILED")
            print(f"Completed before failure: {number - 1}/{total_steps}")
            print(f"Elapsed time: {elapsed:.2f} seconds")
            print("=" * 78)
            return 1

    elapsed = time.perf_counter() - pipeline_started

    print("\n" + "=" * 78)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Successful steps: {total_steps}/{total_steps}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
