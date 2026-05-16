"""
gen_puml_sql.py
---------------
Generates a PlantUML Entity-Relationship diagram from all SQL files
in a given directory (recursive scan).

Parses CREATE TABLE statements and extracts:
  - Column names, types, and NOT NULL constraints
  - Primary key columns
  - Foreign key relationships

Usage:
    python gen_puml_sql.py [sql_dir] [output_file]

Defaults:
    sql_dir     = server/sql
    output_file = diagrams/sql_schema.puml
"""

import os
import re
import sys


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

# Matches: CREATE TABLE [IF NOT EXISTS] table_name (
_RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(",
    re.IGNORECASE,
)

# Matches bare column lines: col_name TYPE [NOT NULL] [DEFAULT ...]
# Does NOT match lines that start with CONSTRAINT / PRIMARY / FOREIGN / CHECK / UNIQUE
_RE_COLUMN = re.compile(
    r"^\s{1,8}(\w+)\s+([\w\(\),]+(?:\s+GENERATED\s+ALWAYS\s+AS\s+IDENTITY)?)"
    r"(?:\s+(NOT\s+NULL))?",
    re.IGNORECASE,
)

# Inline PRIMARY KEY: id BIGINT ... PRIMARY KEY
_RE_INLINE_PK = re.compile(r"\bPRIMARY\s+KEY\b", re.IGNORECASE)

# CONSTRAINT ... PRIMARY KEY (col1, col2, ...)
_RE_TABLE_PK = re.compile(
    r"CONSTRAINT\s+\w+\s+PRIMARY\s+KEY\s*\(([^)]+)\)",
    re.IGNORECASE,
)

# CONSTRAINT ... FOREIGN KEY (col) REFERENCES other_table (ref_col)
_RE_FK = re.compile(
    r"CONSTRAINT\s+(\w+)\s+FOREIGN\s+KEY\s*\(([^)]+)\)"
    r"\s+REFERENCES\s+(\w+)\s*(?:\(([^)]+)\))?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _collect_sql(sql_dir: str) -> str:
    """Recursively read all .sql files under sql_dir and return concatenated content."""
    parts = []
    for root, _dirs, files in os.walk(sql_dir):
        for fname in sorted(files):
            if fname.endswith(".sql"):
                path = os.path.join(root, fname)
                with open(path, encoding="utf-8", errors="replace") as fh:
                    parts.append(fh.read())
    return "\n".join(parts)


def _strip_comments(sql: str) -> str:
    """Remove SQL block comments (/* ... */) and line comments (-- ...)."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _parse_tables(sql: str) -> dict:
    """
    Returns a dict keyed by table name with structure:
      {
        "columns": [(name, type, not_null)],
        "pk_cols": set of column names,
        "fks": [(constraint_name, local_col, ref_table, ref_col)],
      }
    """
    tables = {}

    # Iterate over each CREATE TABLE block
    for match in _RE_CREATE_TABLE.finditer(sql):
        table_name = match.group(1).lower()
        block_start = match.end()  # position of opening '('

        # Walk forward to find the matching closing ')' at depth 0
        depth = 1
        pos = block_start
        while pos < len(sql) and depth > 0:
            ch = sql[pos]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            pos += 1
        block_body = sql[block_start:pos - 1]

        columns = []
        pk_cols = set()
        fks = []

        # Extract PKs from the full block body (CONSTRAINT ... PRIMARY KEY spans multiple lines)
        for pk_match in _RE_TABLE_PK.finditer(block_body):
            for col in pk_match.group(1).split(","):
                pk_cols.add(col.strip().lower())

        # Extract FKs from the full block body (CONSTRAINT ... FOREIGN KEY spans multiple lines)
        for fk_match in _RE_FK.finditer(block_body):
            fks.append((
                fk_match.group(1),
                fk_match.group(2).strip().lower(),
                fk_match.group(3).lower(),
                (fk_match.group(4) or "id").strip().lower(),
            ))

        # Extract columns line-by-line (each column is always a single line)
        for raw_line in block_body.split("\n"):
            line = raw_line.strip().rstrip(",")
            if not line:
                continue

            upper = line.upper()

            # Skip all constraint / keyword-only lines
            if upper.startswith(("CONSTRAINT", "CHECK", "UNIQUE", "INDEX",
                                  "PRIMARY", "FOREIGN", "REFERENCES")):
                continue

            col_match = _RE_COLUMN.match(raw_line)
            if col_match:
                col_name = col_match.group(1).lower()
                col_type = col_match.group(2)
                # Normalise verbose GENERATED ... type suffix
                col_type = re.sub(
                    r"\s+GENERATED\s+ALWAYS\s+AS\s+IDENTITY.*", "", col_type, flags=re.IGNORECASE
                ).strip()
                not_null = bool(col_match.group(3))

                # Check for inline PRIMARY KEY on the same line
                if _RE_INLINE_PK.search(raw_line):
                    pk_cols.add(col_name)
                    not_null = True

                columns.append((col_name, col_type, not_null))

        # Deduplicate columns by name (ALTER TABLE may re-add)
        seen = set()
        unique_cols = []
        for col in columns:
            if col[0] not in seen:
                seen.add(col[0])
                unique_cols.append(col)

        if table_name in tables:
            # Merge extra columns from ALTER TABLE re-runs
            existing_names = {c[0] for c in tables[table_name]["columns"]}
            for col in unique_cols:
                if col[0] not in existing_names:
                    tables[table_name]["columns"].append(col)
            tables[table_name]["pk_cols"].update(pk_cols)
            tables[table_name]["fks"].extend(fks)
        else:
            tables[table_name] = {
                "columns": unique_cols,
                "pk_cols": pk_cols,
                "fks": fks,
            }

    return tables


# ---------------------------------------------------------------------------
# PUML generation
# ---------------------------------------------------------------------------

_TYPE_ABBREV = {
    "bigint": "BIGINT",
    "int": "INT",
    "integer": "INT",
    "varchar": "VARCHAR",
    "text": "TEXT",
    "boolean": "BOOL",
    "bool": "BOOL",
    "date": "DATE",
    "timestamp": "TIMESTAMP",
    "timestamptz": "TIMESTAMPTZ",
    "time": "TIME",
    "jsonb": "JSONB",
    "json": "JSON",
}


def _abbrev_type(raw: str) -> str:
    """Shorten verbose SQL types for diagram readability."""
    base = raw.lower().split("(")[0].strip()
    return _TYPE_ABBREV.get(base, raw.upper())


def _generate_puml(tables: dict) -> str:
    lines = [
        "@startuml sql_schema",
        "' Auto-generated from SQL source files.",
        "' Do not edit manually — re-run gen_puml_sql.py instead.",
        "",
        "skinparam linetype ortho",
        "skinparam entity {",
        "  BackgroundColor #EEF5FF",
        "  BorderColor #336699",
        "  FontName Monospaced",
        "}",
        "",
    ]

    known_tables = set(tables.keys())

    # Emit entity blocks
    for table_name, info in sorted(tables.items()):
        lines.append(f"entity {table_name} {{")
        for col_name, col_type, not_null in info["columns"]:
            is_pk = col_name in info["pk_cols"]
            marker = "* " if is_pk else ("+ " if not_null else "  ")
            suffix = " NOT NULL" if not_null and not is_pk else ""
            lines.append(f"  {marker}{col_name} : {_abbrev_type(col_type)}{suffix}")
        lines.append("}")
        lines.append("")

    # Emit relationships from foreign keys
    lines.append("' --- Relationships ---")
    for table_name, info in sorted(tables.items()):
        for constraint_name, local_col, ref_table, ref_col in info["fks"]:
            if ref_table not in known_tables:
                # Reference to a table defined outside the scanned files
                lines.append(
                    f"' WARN: {table_name}.{local_col} -> {ref_table}.{ref_col}"
                    f" ({constraint_name}) -- ref table not found in scan"
                )
                continue
            # Many-to-one: many rows in table_name reference one row in ref_table
            lines.append(f"{table_name} }}o--|| {ref_table} : {constraint_name}")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    sql_dir = sys.argv[1] if len(sys.argv) > 1 else "server/sql"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "diagrams/sql_schema.puml"

    if not os.path.isdir(sql_dir):
        print(f"ERROR: sql_dir '{sql_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    raw_sql = _collect_sql(sql_dir)
    clean_sql = _strip_comments(raw_sql)
    tables = _parse_tables(clean_sql)

    if not tables:
        print("WARNING: No tables found. Check sql_dir path.", file=sys.stderr)

    puml = _generate_puml(tables)

    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(puml)

    print(f"Generated {len(tables)} table(s) -> {output_file}")


if __name__ == "__main__":
    main()
