"""
gen_puml_sql_split.py
---------------------
Generates a multi-file PlantUML ER diagram from SQL files,
mirroring the old arch_*.puml split architecture:

  arch_db_infrastructure.puml  -- sport_type, venue_type, account_role, page_text, match_status, ladder_rating_function
  arch_db_users.puml           -- account, administrator, player, team_manager, club_owner, availability_block
  arch_db_teams.puml           -- team, team_manager_team, player_team, team_join_request
  arch_db_clubs.puml           -- club, club_owner_club, club_player, club_join_request
  arch_db_ladders.puml         -- ladder, ladder_team
  arch_db_matches.puml         -- match_rule_set, match_proposal, match_accepted, match_rejected,
                                  match_played, match_cancelled, match_score_submission
  arch_db.puml                 -- root include file

Each domain file uses !ifndef / !define guards and !include for dependencies.
Optional notes are wrapped in !ifdef SHOW_COMMENTS blocks.

Usage:
    python gen_puml_sql_split.py [sql_dir] [output_dir]

Defaults:
    sql_dir    = server/sql
    output_dir = diagrams/db
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Domain table map -- which tables belong to which file
# ---------------------------------------------------------------------------

DOMAINS = {
    "infrastructure": [
        "sport_type",
        "venue_type",
        "account_role",
        "match_status",
        "ladder_rating_function",
        "page_text",
    ],
    "users": [
        "account",
        "administrator",
        "player",
        "team_manager",
        "club_owner",
        "availability_block",
    ],
    "teams": [
        "team",
        "team_manager_team",
        "player_team",
        "team_join_request",
    ],
    "clubs": [
        "club",
        "club_owner_club",
        "club_player",
        "club_join_request",
    ],
    "ladders": [
        "ladder",
        "ladder_team",
    ],
    "matches": [
        "match_rule_set",
        "match_proposal",
        "match_accepted",
        "match_rejected",
        "match_played",
        "match_cancelled",
        "match_score_submission",
    ],
}

# Which other domain files does each domain need to !include
DOMAIN_DEPS = {
    "infrastructure": [],
    "users":          ["infrastructure"],
    "teams":          ["users", "infrastructure"],
    "clubs":          ["users", "teams", "matches", "infrastructure"],
    "ladders":        ["users", "matches", "infrastructure", "teams"],
    "matches":        ["teams", "users", "infrastructure"],
}

# Optional notes per table (mirrors SHOW_COMMENTS pattern from old arch)
TABLE_NOTES = {
    "sport_type": (
        "top",
        "Lookup table for sport kinds.\n"
        "min/max player counts constrain team sizes per sport.",
    ),
    "account_role": (
        "top",
        "Static role reference: account, player, team_manager, club_owner, administrator.",
    ),
    "account": (
        "top",
        "Core identity record.\n"
        "Role hierarchy is resolved at runtime via related sub-tables.",
    ),
    "administrator": (
        "top",
        "Site administrators.\n"
        "Can only be assigned by another administrator.\n"
        "access_level controls permission breadth.",
    ),
    "player": (
        "top",
        "Subtype of account.\n"
        "Joins teams via player_team association.",
    ),
    "team_manager": (
        "top",
        "Subtype of account.\n"
        "Manages one or more teams via team_manager_team (with permission flags).",
    ),
    "club_owner": (
        "top",
        "Subtype of team_manager.\n"
        "Manages one or more clubs via club_owner_club (with permission flags).",
    ),
    "availability_block": (
        "top",
        "Weekly recurring availability window for a user.\n"
        "Used by the weekly match proposal generator.",
    ),
    "team": (
        "top",
        "A sports team, optionally linked to a club.\n"
        "sport_type_id must match for teams playing each other.",
    ),
    "team_manager_team": (
        "top",
        "Many-to-many: manager <-> team, with per-team permission flags.",
    ),
    "player_team": (
        "top",
        "Many-to-many: player <-> team membership.",
    ),
    "team_join_request": (
        "top",
        "A player's request to join a team.\n"
        "Only one pending request allowed per (team, user) pair.",
    ),
    "club": (
        "top",
        "A sports club that may contain multiple teams and ladders.",
    ),
    "club_owner_club": (
        "top",
        "Many-to-many: club_owner <-> club, with per-club permission flags.",
    ),
    "club_player": (
        "top",
        "Direct club membership for a player\n"
        "(independent of team membership).",
    ),
    "club_join_request": (
        "top",
        "A user's request to join a club.",
    ),
    "ladder": (
        "top",
        "A competition ladder owned by a club.\n"
        "Binds teams to a ruleset and rating function.",
    ),
    "ladder_team": (
        "top",
        "Team participation in a ladder with rank, rating, and match count.",
    ),
    "match_rule_set": (
        "top",
        "Structured ruleset for a match format (best_of_3, timed, pro_set).\n"
        "Can be shared across clubs or kept private.",
    ),
    "match_proposal": (
        "top",
        "Base record for every match.\n"
        "Extensions (accepted/rejected/played/cancelled) inherit this id.",
    ),
    "match_score_submission": (
        "top",
        "One submission per role (team1_side, team2_side, ladder_admin).\n"
        "Dispute is raised when team sides disagree.",
    ),
    "match_status": (
        "top",
        "Seed values: pending, accepted, rejected, played, cancelled.",
    ),
}


# ---------------------------------------------------------------------------
# SQL parsing (reused from gen_puml_sql.py)
# ---------------------------------------------------------------------------

_RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(",
    re.IGNORECASE,
)
_RE_COLUMN = re.compile(
    r"^\s{1,8}(\w+)\s+([\w\(\),]+(?:\s+GENERATED\s+ALWAYS\s+AS\s+IDENTITY)?)"
    r"(?:\s+(NOT\s+NULL))?",
    re.IGNORECASE,
)
_RE_INLINE_PK  = re.compile(r"\bPRIMARY\s+KEY\b", re.IGNORECASE)
_RE_TABLE_PK   = re.compile(r"CONSTRAINT\s+\w+\s+PRIMARY\s+KEY\s*\(([^)]+)\)", re.IGNORECASE)
_RE_FK         = re.compile(
    r"CONSTRAINT\s+(\w+)\s+FOREIGN\s+KEY\s*\(([^)]+)\)"
    r"\s+REFERENCES\s+(\w+)\s*(?:\(([^)]+)\))?",
    re.IGNORECASE,
)


def _collect_sql(sql_dir: str) -> str:
    parts = []
    for root, _dirs, files in os.walk(sql_dir):
        for fname in sorted(files):
            if fname.endswith(".sql"):
                path = os.path.join(root, fname)
                with open(path, encoding="utf-8", errors="replace") as fh:
                    parts.append(fh.read())
    return "\n".join(parts)


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _parse_tables(sql: str) -> dict:
    tables = {}
    for match in _RE_CREATE_TABLE.finditer(sql):
        table_name = match.group(1).lower()
        block_start = match.end()
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

        columns  = []
        pk_cols  = set()
        fks      = []

        for pk_m in _RE_TABLE_PK.finditer(block_body):
            for col in pk_m.group(1).split(","):
                pk_cols.add(col.strip().lower())

        for fk_m in _RE_FK.finditer(block_body):
            fks.append((
                fk_m.group(1),
                fk_m.group(2).strip().lower(),
                fk_m.group(3).lower(),
                (fk_m.group(4) or "id").strip().lower(),
            ))

        for raw_line in block_body.split("\n"):
            line  = raw_line.strip().rstrip(",")
            upper = line.upper()
            if not line:
                continue
            if upper.startswith(("CONSTRAINT", "CHECK", "UNIQUE", "INDEX",
                                  "PRIMARY", "FOREIGN", "REFERENCES")):
                continue
            col_m = _RE_COLUMN.match(raw_line)
            if col_m:
                col_name = col_m.group(1).lower()
                col_type = col_m.group(2)
                col_type = re.sub(
                    r"\s+GENERATED\s+ALWAYS\s+AS\s+IDENTITY.*", "", col_type,
                    flags=re.IGNORECASE,
                ).strip()
                not_null = bool(col_m.group(3))
                if _RE_INLINE_PK.search(raw_line):
                    pk_cols.add(col_name)
                    not_null = True
                columns.append((col_name, col_type, not_null))

        seen   = set()
        unique = []
        for col in columns:
            if col[0] not in seen:
                seen.add(col[0])
                unique.append(col)

        if table_name in tables:
            existing_names = {c[0] for c in tables[table_name]["columns"]}
            for col in unique:
                if col[0] not in existing_names:
                    tables[table_name]["columns"].append(col)
            tables[table_name]["pk_cols"].update(pk_cols)
            tables[table_name]["fks"].extend(fks)
        else:
            tables[table_name] = {"columns": unique, "pk_cols": pk_cols, "fks": fks}

    return tables


# ---------------------------------------------------------------------------
# PUML helpers
# ---------------------------------------------------------------------------

_TYPE_ABBREV = {
    "bigint": "BIGINT", "int": "INT", "integer": "INT",
    "varchar": "VARCHAR", "text": "TEXT", "boolean": "BOOL", "bool": "BOOL",
    "date": "DATE", "timestamp": "TIMESTAMP", "timestamptz": "TIMESTAMPTZ",
    "time": "TIME", "jsonb": "JSONB", "json": "JSON",
}


def _abbrev(raw: str) -> str:
    base = raw.lower().split("(")[0].strip()
    return _TYPE_ABBREV.get(base, raw.upper())


def _entity_block(table_name: str, info: dict) -> list:
    lines = [f"entity {table_name} {{"]
    for col_name, col_type, not_null in info["columns"]:
        is_pk  = col_name in info["pk_cols"]
        marker = "* " if is_pk else ("+ " if not_null else "  ")
        suffix = " NOT NULL" if not_null and not is_pk else ""
        lines.append(f"  {marker}{col_name} : {_abbrev(col_type)}{suffix}")
    lines.append("}")
    return lines


def _fk_lines(table_name: str, info: dict, known: set) -> list:
    lines = []
    for constraint, local_col, ref_table, _ref_col in info["fks"]:
        if ref_table in known:
            lines.append(f"{table_name} }}o--|| {ref_table} : {constraint}")
    return lines


def _note_lines(table_name: str, position: str, text: str) -> list:
    escaped = text.replace("\n", "\\n")
    lines   = [f"note {position} of {table_name}"]
    for row in text.split("\n"):
        lines.append(f"  {row}")
    lines.append("end note")
    return lines


# ---------------------------------------------------------------------------
# Per-domain file generator
# ---------------------------------------------------------------------------

def _domain_file(
    domain: str,
    table_names: list,
    all_tables: dict,
    deps: list,
) -> str:
    guard   = f"DB_{domain.upper()}_BLOCK"
    include_lines = [f"  !include arch_db_{dep}.puml" for dep in deps]

    lines = [
        "@startuml",
        f"!ifndef {guard}",
        f"!define {guard}",
        "",
        "skinparam linetype ortho",
        "skinparam groupInheritance 2",
    ]

    if include_lines:
        lines += include_lines
        lines.append("")

    # Entity definitions
    for tname in table_names:
        if tname not in all_tables:
            lines.append(f"' WARNING: table {tname!r} not found in SQL sources")
            continue
        lines += _entity_block(tname, all_tables[tname])
        lines.append("")

    # FK relationships (within this file or to included files)
    # Collect all tables visible in this file + its deps
    visible = set(table_names)
    dep_stack = list(deps)
    while dep_stack:
        d = dep_stack.pop()
        visible.update(DOMAINS.get(d, []))
        dep_stack.extend(DOMAIN_DEPS.get(d, []))

    rel_lines = []
    for tname in table_names:
        if tname not in all_tables:
            continue
        rel_lines += _fk_lines(tname, all_tables[tname], visible)

    if rel_lines:
        lines.append("' --- Relationships ---")
        lines += rel_lines
        lines.append("")

    # SHOW_COMMENTS block
    comment_tables = [t for t in table_names if t in TABLE_NOTES]
    if comment_tables:
        lines.append("!ifdef SHOW_COMMENTS")
        lines.append("")
        for tname in comment_tables:
            pos, text = TABLE_NOTES[tname]
            lines += _note_lines(tname, pos, text)
            lines.append("")
        lines.append("!endif")
        lines.append("")

    lines.append(f"!endif")
    lines.append("@enduml")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Root include file
# ---------------------------------------------------------------------------

def _root_file() -> str:
    lines = [
        "@startuml arch_db",
        "",
        "skinparam linetype ortho",
        "skinparam groupInheritance 2",
        "",
        "' Uncomment the line below to display design notes",
        "' !define SHOW_COMMENTS",
        "",
    ]
    for domain in DOMAINS:
        lines.append(f"!include arch_db_{domain}.puml")
    lines += ["", "@enduml", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    sql_dir    = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(BASE_DIR, "..", "sql"))
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.normpath(
        os.path.join(BASE_DIR, "..", "..", "diagrams", "db"))

    sql_dir = sys.argv[1] if len(sys.argv) > 1 else "server/sql"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "diagrams/db"

    if not os.path.isdir(sql_dir):
        print(f"ERROR: sql_dir '{sql_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    raw_sql    = _collect_sql(sql_dir)
    clean_sql  = _strip_comments(raw_sql)
    all_tables = _parse_tables(clean_sql)

    # Write per-domain files
    for domain, table_names in DOMAINS.items():
        deps    = DOMAIN_DEPS[domain]
        content = _domain_file(domain, table_names, all_tables, deps)
        out_path = os.path.join(output_dir, f"arch_db_{domain}.puml")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  {out_path}  ({len(table_names)} tables)")

    # Write root file
    root_path = os.path.join(output_dir, "arch_db.puml")
    with open(root_path, "w", encoding="utf-8") as fh:
        fh.write(_root_file())
    print(f"  {root_path}  (root include)")

    print(f"\nDone. {len(DOMAINS) + 1} files -> {output_dir}")


if __name__ == "__main__":
    main()
