"""
gen_puml_routes_split.py
------------------------
Generates a multi-file PlantUML component diagram from Flask route files,
mirroring the old arch_*.puml split architecture:

  arch_routes_auth.puml         -- authentication & profile
  arch_routes_users.puml        -- availability, dashboard, achievements
  arch_routes_clubs.puml        -- clubs CRUD, owners, members, join-requests
  arch_routes_teams.puml        -- teams CRUD, membership, join-requests, permissions
  arch_routes_ladders.puml      -- ladder management, team enrollment
  arch_routes_matches.puml      -- match proposals, accept/reject, score, disputes
  arch_routes_infrastructure.puml -- sport types, rating functions, rule-sets, weather, health
  arch_routes.puml              -- root include file

Each file uses !ifndef / !define guards and !include for dependencies.
Optional notes wrapped in !ifdef SHOW_COMMENTS.

Usage:
    python gen_puml_routes_split.py [routes_dir] [app_factory] [output_dir]

Defaults:
    routes_dir   = server/app/routes
    app_factory  = server/app/__init__.py
    output_dir   = diagrams/routes
"""

import ast
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Domain -> blueprint variable names
# ---------------------------------------------------------------------------

DOMAINS = {
    "auth": {
        "blueprints": ["auth_bp"],
        "deps":       [],
        "notes": {
            "auth_bp": (
                "Authentication endpoints.\n"
                "Handles signup, login/logout, email verification,\n"
                "password reset, and current-user profile (GET/PATCH)."
            ),
        },
    },
    "users": {
        "blueprints": ["availability_bp", "dashboard_bp"],
        "deps":       ["auth"],
        "notes": {
            "availability_bp": (
                "Weekly availability blocks for the current user.\n"
                "Used by the automated match proposal generator."
            ),
            "dashboard_bp": (
                "Personal dashboard, achievements, and club join-request flow."
            ),
        },
    },
    "clubs": {
        "blueprints": ["clubs_bp", "city_bp"],
        "deps":       ["auth"],
        "notes": {
            "clubs_bp": (
                "Full CRUD for clubs, plus owner and member management.\n"
                "Also exposes /api/accounts/search used during owner assignment."
            ),
            "city_bp": (
                "City autocomplete — used in club creation form."
            ),
        },
    },
    "teams": {
        "blueprints": ["team_bp"],
        "deps":       ["auth", "clubs"],
        "notes": {
            "team_bp": (
                "Team CRUD (core), player/manager membership,\n"
                "join-request accept/reject, permission queries,\n"
                "and ladder-peer discovery — all nested under /api/teams."
            ),
        },
    },
    "ladders": {
        "blueprints": ["ladders_bp", "ladder_bp"],
        "deps":       ["auth", "clubs", "teams"],
        "notes": {
            "ladders_bp": (
                "List ladders for a club and top-player ranking."
            ),
            "ladder_bp": (
                "Ladder detail, player list, eligible-team query,\n"
                "and team enrollment into a ladder."
            ),
        },
    },
    "matches": {
        "blueprints": [
            "matches_bp",
            "match_proposals_bp",
            "match_rule_set_bp",
            "match_rule_bp",
        ],
        "deps": ["auth", "teams", "ladders"],
        "notes": {
            "matches_bp": (
                "Core match lifecycle: propose, accept, reject, cancel.\n"
                "Score submission and dispute resolution.\n"
                "List views: active, pending, played, awaiting-result."
            ),
            "match_proposals_bp": (
                "Proposal management: create, list, update status.\n"
                "Weekly auto-proposal generation trigger."
            ),
            "match_rule_set_bp": (
                "Full CRUD for structured match rule-sets\n"
                "(format, deuce rule, game format, etc.)."
            ),
        },
    },
    "infrastructure": {
        "blueprints": [
            "sport_type_bp",
            "rating_function_bp",
            "rule_set_bp",
            "weather",
            "api",
        ],
        "deps": [],
        "notes": {
            "sport_type_bp": "Lookup: available sport types.",
            "rating_function_bp": "Lookup: available ladder rating functions.",
            "rule_set_bp": "Legacy rule-set list endpoint (deprecated path).",
            "weather": (
                "Weather data for a club's location.\n"
                "Used by the match scheduling UI."
            ),
            "api": "Health check endpoint.",
        },
    },
}

DOMAIN_DEPS = {d: info["deps"] for d, info in DOMAINS.items()}


# ---------------------------------------------------------------------------
# Route parsing (shared with gen_puml_routes.py)
# ---------------------------------------------------------------------------

_SHORTHAND = {
    "get": ["GET"], "post": ["POST"], "put": ["PUT"],
    "patch": ["PATCH"], "delete": ["DELETE"],
    "head": ["HEAD"], "options": ["OPTIONS"],
}


@dataclass
class RouteEntry:
    path:    str
    methods: list


@dataclass
class BlueprintInfo:
    var_name:   str
    bp_name:    str
    url_prefix: str
    routes:     list = field(default_factory=list)
    children:   list = field(default_factory=list)


def _const_str(node) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_func_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _get_kwarg_str(node: ast.Call, key: str) -> Optional[str]:
    for kw in node.keywords:
        if kw.arg == key:
            return _const_str(kw.value)
    return None


def _methods_from_decorator(node: ast.Call) -> list:
    func_name = _call_func_name(node).lower()
    if func_name in _SHORTHAND:
        return _SHORTHAND[func_name]
    if func_name == "route":
        for kw in node.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                return [_const_str(el).upper() for el in kw.value.elts if _const_str(el)]
        return ["GET"]
    return []


def _parse_route_file(path: str) -> list:
    with open(path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []

    blueprints: dict = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if _call_func_name(node.value) != "Blueprint":
            continue
        call = node.value
        if not call.args:
            continue
        bp_name    = _const_str(call.args[0]) or ""
        url_prefix = _get_kwarg_str(call, "url_prefix") or ""
        for target in node.targets:
            if isinstance(target, ast.Name):
                blueprints[target.id] = BlueprintInfo(
                    var_name=target.id, bp_name=bp_name, url_prefix=url_prefix,
                )

    if not blueprints:
        return []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute):
                continue
            if not isinstance(func.value, ast.Name):
                continue
            bp_var  = func.value.id
            if bp_var not in blueprints:
                continue
            methods = _methods_from_decorator(decorator)
            if not methods or not decorator.args:
                continue
            route_path = _const_str(decorator.args[0])
            if route_path is None:
                continue
            blueprints[bp_var].routes.append(RouteEntry(path=route_path, methods=methods))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if _call_func_name(call) != "register_blueprint":
            continue
        func = call.func
        if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
            continue
        parent_var = func.value.id
        if parent_var not in blueprints or not call.args:
            continue
        child_arg = call.args[0]
        if isinstance(child_arg, ast.Name):
            blueprints[parent_var].children.append(child_arg.id)

    return list(blueprints.values())


def _collect_all_blueprints(routes_dir: str) -> dict:
    all_bps: dict = {}
    for root, _dirs, files in os.walk(routes_dir):
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            for bp in _parse_route_file(os.path.join(root, fname)):
                if bp.var_name in all_bps:
                    existing = all_bps[bp.var_name]
                    existing.routes.extend(bp.routes)
                    for child in bp.children:
                        if child not in existing.children:
                            existing.children.append(child)
                else:
                    all_bps[bp.var_name] = bp
    return all_bps


def _resolve_prefixes(all_bps: dict) -> None:
    child_to_parent: dict = {}
    for var_name, bp in all_bps.items():
        for child in bp.children:
            child_to_parent[child] = var_name

    def full_prefix(var_name: str, visited: set) -> str:
        if var_name in visited:
            return ""
        visited.add(var_name)
        bp = all_bps.get(var_name)
        if bp is None:
            return ""
        parent = child_to_parent.get(var_name)
        if parent is None:
            return bp.url_prefix
        return full_prefix(parent, visited) + bp.url_prefix

    for var_name, bp in all_bps.items():
        bp.url_prefix = full_prefix(var_name, set())


def _safe_id(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", text)


# ---------------------------------------------------------------------------
# PUML generation helpers
# ---------------------------------------------------------------------------

def _method_label(methods: list) -> str:
    return " | ".join(methods)


def _route_component_lines(bp: BlueprintInfo, indent: str) -> list:
    lines = []
    for route in sorted(bp.routes, key=lambda r: r.path):
        full_path  = (bp.url_prefix + route.path).replace("//", "/") or "/"
        method_str = _method_label(route.methods)
        comp_id    = _safe_id(f"r_{bp.var_name}_{full_path}_{method_str}")
        lines.append(f"{indent}  [{method_str}  {full_path}] as {comp_id}")
    return lines


def _bp_package_lines(
    bp: BlueprintInfo,
    all_bps: dict,
    indent: str = "",
) -> list:
    lines   = []
    pkg_id  = _safe_id(f"pkg_{bp.var_name}")
    prefix  = bp.url_prefix or "/"
    lines.append(f'{indent}package "{bp.bp_name}  ({prefix})" as {pkg_id} {{')
    lines += _route_component_lines(bp, indent)
    for child_var in bp.children:
        if child_var in all_bps:
            lines += _bp_package_lines(all_bps[child_var], all_bps, indent + "  ")
    lines.append(f"{indent}}}")
    return lines


# ---------------------------------------------------------------------------
# Per-domain file generator
# ---------------------------------------------------------------------------

def _domain_file(
    domain: str,
    bp_var_names: list,
    all_bps: dict,
    deps: list,
    notes: dict,
) -> str:
    guard         = f"ROUTES_{domain.upper()}_BLOCK"
    include_lines = [f"  !include arch_routes_{dep}.puml" for dep in deps]

    lines = [
        "@startuml",
        f"!ifndef {guard}",
        f"!define {guard}",
        "",
        "skinparam component {",
        "  BackgroundColor #FFFDE7",
        "  BorderColor #F57F17",
        "  FontName Monospaced",
        "}",
        "skinparam package {",
        "  BackgroundColor #FFF8E1",
        "  BorderColor #F9A825",
        "}",
        "",
    ]

    if include_lines:
        lines += include_lines
        lines.append("")

    # Emit package blocks
    for var_name in bp_var_names:
        bp = all_bps.get(var_name)
        if bp is None:
            lines.append(f"' WARNING: blueprint {var_name!r} not found in scan")
            continue
        lines += _bp_package_lines(bp, all_bps)
        lines.append("")

    # SHOW_COMMENTS block
    note_bps = [v for v in bp_var_names if v in notes]
    if note_bps:
        lines.append("!ifdef SHOW_COMMENTS")
        lines.append("")
        for var_name in note_bps:
            pkg_id = _safe_id(f"pkg_{var_name}")
            lines.append(f"note top of {pkg_id}")
            for row in notes[var_name].split("\n"):
                lines.append(f"  {row}")
            lines.append("end note")
            lines.append("")
        lines.append("!endif")
        lines.append("")

    lines.append("!endif")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Root include file
# ---------------------------------------------------------------------------

def _root_file() -> str:
    lines = [
        "@startuml arch_routes",
        "",
        "skinparam groupInheritance 2",
        "!pragma layout smetana",
        "",
        "legend right",
        "  GET    : read",
        "  POST   : create / action",
        "  PUT    : full replace",
        "  PATCH  : partial update",
        "  DELETE : remove",
        "endlegend",
        "",
        "' Uncomment to display design notes",
        "' !define SHOW_COMMENTS",
        "",
    ]
    for domain in DOMAINS:
        lines.append(f"!include arch_routes_{domain}.puml")
    lines += ["", "@enduml", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    routes_dir       = sys.argv[1] if len(sys.argv) > 1 else "server/app/routes"
    output_dir      = sys.argv[3] if len(sys.argv) > 3 else "diagrams/routes"

    if not os.path.isdir(routes_dir):
        print(f"ERROR: routes_dir '{routes_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    all_bps = _collect_all_blueprints(routes_dir)
    _resolve_prefixes(all_bps)

    for domain, info in DOMAINS.items():
        bp_var_names = info["blueprints"]
        deps         = info["deps"]
        notes        = info["notes"]
        content      = _domain_file(domain, bp_var_names, all_bps, deps, notes)
        out_path     = os.path.join(output_dir, f"arch_routes_{domain}.puml")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        route_count = sum(
            len(all_bps[v].routes)
            for v in bp_var_names
            if v in all_bps
        )
        print(f"  {out_path}  ({route_count} routes)")

    root_path = os.path.join(output_dir, "arch_routes.puml")
    with open(root_path, "w", encoding="utf-8") as fh:
        fh.write(_root_file())
    print(f"  {root_path}  (root include)")

    print(f"\nDone. {len(DOMAINS) + 1} files -> {output_dir}")


if __name__ == "__main__":
    main()
