import sqlite3
from pathlib import Path

db_path = Path("database") / "offshore_field_development_economics.db"

if not db_path.exists():
    raise FileNotFoundError(f"Database not found: {db_path.resolve()}")

with sqlite3.connect(db_path) as connection:
    objects = connection.execute("""
        SELECT type, name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
    """).fetchall()

    print("=" * 80)
    print("PROJECT 3 — SQLITE DATABASE SOURCE INVENTORY")
    print("=" * 80)

    for object_type, name in objects:
        columns = connection.execute(
            f'PRAGMA table_info("{name}")'
        ).fetchall()

        print(f"\n{object_type.upper()}: {name}")
        print("-" * 80)

        for column in columns:
            print(f"  {column[1]}")

    print("\n" + "=" * 80)
    print(f"Total tables and views: {len(objects)}")
