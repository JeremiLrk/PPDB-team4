"""
gen_puml_routes.py
------------------
Generates a PlantUML component / package diagram that shows all HTTP
routes registered in the Flask application, grouped by Blueprint.

Scans all *.py files under a given routes directory (recursive) and
extracts:
  - Blueprint names and their url_prefix values
  - Route paths and HTTP methods (from @bp.route / @bp.get / @bp.post etc.)
  - register_blueprint() nesting so child blueprints inherit their parent prefix

Additionally reads the app factory file to resolve which blueprints are
actually registered in create_app().

Usage:
    python gen_puml_routes.py [routes_dir] [app_factory_file] [output_file]

Defaults:
    routes_dir        = server/app/routes
    app_factory_file  = server/app/__init__.py
    output_file       = diagrams/routes.puml
"""

import ast
import os
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RouteEntry:
    path: str           # full path including prefix
    methods: list       # ["GET", "POST", ...]


@dataclass
class BlueprintInfo:
    var_name: str               # Python variable name, e.g. "auth_bp"
    bp_name: str                # Blueprint("auth", ...) first arg
    url_prefix: str             # e.g. "/api"
    routes: list = field(default_factory=list)   # list of RouteEntry
    children: list = field(default_factory=list) # var names of registered sub-blueprints


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Route-decorator method extraction
# ---------------------------------------------------------------------------

# Mapping of shorthand decorator names to HTTP methods
_SHORTHAND = {
    "get": ["GET"],
    "post": ["POST"],
    "put": ["PUT"],
    "patch": ["PATCH"],
    "delete": ["DELETE"],
    "head": ["HEAD"],
    "options": ["OPTIONS"],
}


def _methods_from_decorator(node: ast.Call) -> list:
    """
    Extract HTTP methods from a @bp.route(..., methods=[...]) or
    @bp.get(...) style decorator call.
    """
    func_name = _call_func_name(node).lower()

    if func_name in _SHORTHAND:
        return _SHORTHAND[func_name]

    if func_name == "route":
        # Look for methods=[...] keyword argument
        for kw in node.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                return [
                    _const_str(el).upper()
                    for el in kw.value.elts
                    if _const_str(el)
                ]
        # No methods specified -> defaults to GET
        return ["GET"]

    return []


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------

def _parse_route_file(path: str) -> list[BlueprintInfo]:
    """
    Parse a single Python file and return all Blueprint definitions
    together with their route registrations and child blueprint registrations.
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []

    blueprints: dict[str, BlueprintInfo] = {}  # var_name -> BlueprintInfo

    # First pass: find Blueprint(...) assignments
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

        bp_name = _const_str(call.args[0]) or ""
        url_prefix = _get_kwarg_str(call, "url_prefix") or ""

        for target in node.targets:
            if isinstance(target, ast.Name):
                blueprints[target.id] = BlueprintInfo(
                    var_name=target.id,
                    bp_name=bp_name,
                    url_prefix=url_prefix,
                )

    if not blueprints:
        return []

    # Second pass: find route decorators on function definitions
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            # Must be attribute access: bp_var.route / bp_var.get / etc.
            if not isinstance(func, ast.Attribute):
                continue
            if not isinstance(func.value, ast.Name):
                continue

            bp_var = func.value.id
            if bp_var not in blueprints:
                continue

            methods = _methods_from_decorator(decorator)
            if not methods:
                continue

            # Route path is the first positional argument
            if not decorator.args:
                continue
            route_path = _const_str(decorator.args[0])
            if route_path is None:
                continue

            blueprints[bp_var].routes.append(
                RouteEntry(path=route_path, methods=methods)
            )

    # Third pass: find register_blueprint() calls on blueprint variables
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if _call_func_name(call) != "register_blueprint":
            continue
        func = call.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name):
            continue

        parent_var = func.value.id
        if parent_var not in blueprints:
            continue

        if not call.args:
            continue
        child_arg = call.args[0]
        if isinstance(child_arg, ast.Name):
            blueprints[parent_var].children.append(child_arg.id)

    return list(blueprints.values())


def _collect_all_blueprints(routes_dir: str) -> dict[str, BlueprintInfo]:
    """
    Recursively scan routes_dir and return all BlueprintInfo objects
    indexed by var_name.  Merge if the same var_name appears in multiple files.
    """
    all_bps: dict[str, BlueprintInfo] = {}

    for root, _dirs, files in os.walk(routes_dir):
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            for bp in _parse_route_file(path):
                if bp.var_name in all_bps:
                    existing = all_bps[bp.var_name]
                    existing.routes.extend(bp.routes)
                    for child in bp.children:
                        if child not in existing.children:
                            existing.children.append(child)
                else:
                    all_bps[bp.var_name] = bp

    return all_bps


def _resolve_prefixes(all_bps: dict[str, BlueprintInfo]) -> None:
    """
    Walk the child relationships and prepend parent prefixes to children.
    Operates in-place.  Handles nested blueprints (recursive).
    """
    # Build a reverse map: child var_name -> parent var_name
    child_to_parent: dict[str, str] = {}
    for var_name, bp in all_bps.items():
        for child in bp.children:
            child_to_parent[child] = var_name

    # Resolve full prefix for each blueprint by climbing the parent chain
    def full_prefix(var_name: str, visited: set) -> str:
        if var_name in visited:
            return ""  # Cycle guard
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


def _read_registered_blueprints(app_factory_file: str) -> set:
    """
    Parse the app factory file and return the set of variable names
    passed to app.register_blueprint(...).
    """
    if not os.path.isfile(app_factory_file):
        return set()

    with open(app_factory_file, encoding="utf-8", errors="replace") as fh:
        source = fh.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()

    registered = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if _call_func_name(call) != "register_blueprint":
            continue
        if not call.args:
            continue
        arg = call.args[0]
        if isinstance(arg, ast.Name):
            registered.add(arg.id)

    return registered


# ---------------------------------------------------------------------------
# PUML generation
# ---------------------------------------------------------------------------

_METHOD_COLOR = {
    "GET":    "#AEDFF7",
    "POST":   "#B8F0B8",
    "PUT":    "#FFE0A0",
    "PATCH":  "#FFD0A0",
    "DELETE": "#FFB0B0",
    "HEAD":   "#E0E0E0",
    "OPTIONS":"#E0E0E0",
}


def _method_label(methods: list) -> str:
    return " | ".join(methods)


def _safe_id(text: str) -> str:
    """Convert arbitrary string to a PlantUML-safe identifier."""
    return re.sub(r"[^A-Za-z0-9_]", "_", text)


import re as _re


def _safe_id(text: str) -> str:
    return _re.sub(r"[^A-Za-z0-9_]", "_", text)


def _generate_puml(all_bps: dict[str, BlueprintInfo], registered: set) -> str:
    lines = [
        "@startuml routes",
        "' Auto-generated from Flask route files.",
        "' Do not edit manually — re-run gen_puml_routes.py instead.",
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
        "skinparam linetype polyline",
        "",
        "legend right",
        "  GET    = blue",
        "  POST   = green",
        "  PUT    = orange",
        "  PATCH  = dark orange",
        "  DELETE = red",
        "endlegend",
        "",
    ]

    # Determine which blueprints are top-level (not children of any other)
    all_children: set = set()
    for bp in all_bps.values():
        all_children.update(bp.children)

    top_level = [
        var for var in all_bps
        if var not in all_children
    ]

    def emit_bp(var_name: str, indent: int = 0):
        bp = all_bps.get(var_name)
        if bp is None:
            return

        pad = "  " * indent
        pkg_id = _safe_id(f"pkg_{var_name}")
        prefix_label = bp.url_prefix or "/"
        reg_marker = "" if (var_name in registered or indent > 0) else " [NOT REGISTERED]"

        lines.append(f"{pad}package \"{bp.bp_name}  ({prefix_label}){reg_marker}\" as {pkg_id} {{")

        for route in sorted(bp.routes, key=lambda r: r.path):
            full_path = (bp.url_prefix + route.path).replace("//", "/") or "/"
            method_str = _method_label(route.methods)
            comp_id = _safe_id(f"route_{var_name}_{full_path}_{method_str}")
            lines.append(f'{pad}  [{method_str}  {full_path}] as {comp_id}')

        # Recurse into child blueprints
        for child_var in bp.children:
            emit_bp(child_var, indent + 1)

        lines.append(f"{pad}}}")
        lines.append("")

    for var_name in sorted(top_level):
        emit_bp(var_name)

    lines.append("@enduml")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    routes_dir       = sys.argv[1] if len(sys.argv) > 1 else "server/app/routes"
    app_factory_file = sys.argv[2] if len(sys.argv) > 2 else "server/app/__init__.py"
    output_file      = sys.argv[3] if len(sys.argv) > 3 else "diagrams/routes.puml"

    if not os.path.isdir(routes_dir):
        print(f"ERROR: routes_dir '{routes_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    all_bps = _collect_all_blueprints(routes_dir)
    _resolve_prefixes(all_bps)
    registered = _read_registered_blueprints(app_factory_file)

    total_routes = sum(len(bp.routes) for bp in all_bps.values())
    puml = _generate_puml(all_bps, registered)

    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(puml)

    print(
        f"Generated {len(all_bps)} blueprint(s), "
        f"{total_routes} route(s) -> {output_file}"
    )


if __name__ == "__main__":
    main()
