"""
gen_puml_models.py
------------------
Generates a PlantUML class diagram from SQLAlchemy model files.

Scans all *.py files under a given models directory (recursive).
Extracts:
  - Class names and their __tablename__
  - db.Column fields with type and nullable info
  - db.relationship associations (direction inferred from uselist flag)
  - Inheritance (class Foo(Bar) -> Bar is the parent model)

Usage:
    python gen_puml_models.py [models_dir] [output_file]

Defaults:
    models_dir  = server/app/models
    output_file = diagrams/models.puml
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
class ColumnInfo:
    name: str
    col_type: str        # e.g. "BigInteger", "String(64)"
    nullable: bool       # True when nullable=True or no explicit NOT NULL
    primary_key: bool
    fk_target: Optional[str]  # e.g. "account.id"


@dataclass
class RelationshipInfo:
    attr_name: str
    target_class: str
    is_list: bool        # True when uselist=True (default) -> one-to-many
    back_populates: Optional[str]


@dataclass
class ModelInfo:
    class_name: str
    table_name: Optional[str]
    columns: list = field(default_factory=list)
    relationships: list = field(default_factory=list)
    parent_classes: list = field(default_factory=list)  # Python base class names


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _const_value(node) -> Optional[str]:
    """Return the string/number value of a Constant node, or None."""
    if isinstance(node, ast.Constant):
        return str(node.value)
    return None


def _call_func_name(node: ast.Call) -> str:
    """Return dotted name of the callable, e.g. 'db.Column'."""
    func = node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            return f"{func.value.id}.{func.attr}"
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _get_kwarg(node: ast.Call, key: str):
    """Return the AST node for keyword argument *key* in a Call, or None."""
    for kw in node.keywords:
        if kw.arg == key:
            return kw.value
    return None


def _bool_kwarg(node: ast.Call, key: str, default: bool) -> bool:
    kw = _get_kwarg(node, key)
    if kw is None:
        return default
    if isinstance(kw, ast.Constant):
        return bool(kw.value)
    if isinstance(kw, ast.NameConstant):  # Python < 3.8 compat
        return bool(kw.value)
    return default


def _str_kwarg(node: ast.Call, key: str) -> Optional[str]:
    kw = _get_kwarg(node, key)
    if kw is None:
        return None
    return _const_value(kw)


def _extract_col_type(args: list) -> str:
    """
    Extract the column type from db.Column positional arguments.
    Handles nested calls like db.String(64), db.ForeignKey(...).
    Returns the first non-ForeignKey type argument.
    """
    for arg in args:
        if isinstance(arg, ast.Call):
            name = _call_func_name(arg)
            lower = name.lower()
            if "foreignkey" in lower:
                continue
            # Strip the 'db.' prefix for readability
            label = name.replace("db.", "")
            # Append size if first positional arg is a constant
            if arg.args:
                first = _const_value(arg.args[0])
                if first:
                    label = f"{label}({first})"
            return label
        if isinstance(arg, ast.Attribute):
            return arg.attr
        if isinstance(arg, ast.Name):
            return arg.id
    return "?"


def _extract_fk_target(args: list) -> Optional[str]:
    """Return the ForeignKey target string e.g. 'account.id', if present."""
    for arg in args:
        if isinstance(arg, ast.Call):
            name = _call_func_name(arg)
            if "foreignkey" in name.lower() and arg.args:
                return _const_value(arg.args[0])
    return None


def _parse_column(attr_name: str, call: ast.Call) -> Optional[ColumnInfo]:
    """Parse a db.Column(...) call into a ColumnInfo."""
    col_type = _extract_col_type(call.args)
    nullable = _bool_kwarg(call, "nullable", default=True)
    primary_key = _bool_kwarg(call, "primary_key", default=False)
    fk_target = _extract_fk_target(call.args)

    return ColumnInfo(
        name=attr_name,
        col_type=col_type,
        nullable=nullable,
        primary_key=primary_key,
        fk_target=fk_target,
    )


def _parse_relationship(attr_name: str, call: ast.Call) -> Optional[RelationshipInfo]:
    """Parse a db.relationship(...) call into a RelationshipInfo."""
    # First positional arg is the target class name (string)
    target = None
    if call.args:
        target = _const_value(call.args[0])
    if target is None:
        target = _str_kwarg(call, "argument")  # older style

    if not target:
        return None

    # uselist=False means scalar (one-to-one or many-to-one)
    is_list = _bool_kwarg(call, "uselist", default=True)
    back_populates = _str_kwarg(call, "back_populates")

    return RelationshipInfo(
        attr_name=attr_name,
        target_class=target,
        is_list=is_list,
        back_populates=back_populates,
    )


# ---------------------------------------------------------------------------
# File-level model extraction
# ---------------------------------------------------------------------------

def _parse_model_file(path: str) -> list[ModelInfo]:
    """Parse a single Python file and return all SQLAlchemy Model classes found."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []

    models = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Only collect classes that inherit from db.Model or Model
        parent_names = []
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                parent_names.append(base.attr)
            elif isinstance(base, ast.Name):
                parent_names.append(base.id)

        is_model = any(n in ("Model", "db.Model") for n in parent_names) or \
                   any("model" in n.lower() for n in parent_names)

        # Also include classes that look like SQLAlchemy models even if they
        # inherit from another local model class (e.g. Player(db.Model)).
        # We relax this: collect all classes that have at least one db.Column.

        info = ModelInfo(
            class_name=node.name,
            table_name=None,
            parent_classes=parent_names,
        )

        has_column = False

        for item in node.body:
            # Class-level assignments: name = db.Column(...) or db.relationship(...)
            if not isinstance(item, ast.Assign):
                continue
            for target in item.targets:
                if not isinstance(target, ast.Name):
                    continue
                attr_name = target.id
                value = item.value

                if not isinstance(value, ast.Call):
                    # Check for __tablename__ = "..."
                    if attr_name == "__tablename__":
                        raw = _const_value(value)
                        if raw:
                            info.table_name = raw
                    continue

                func_name = _call_func_name(value)

                if attr_name == "__tablename__":
                    info.table_name = _const_value(value)
                    continue

                lower_func = func_name.lower()

                if "column" in lower_func:
                    col = _parse_column(attr_name, value)
                    if col:
                        has_column = True
                        info.columns.append(col)
                elif "relationship" in lower_func:
                    rel = _parse_relationship(attr_name, value)
                    if rel:
                        info.relationships.append(rel)

        if has_column or is_model:
            models.append(info)

    return models


def _collect_models(models_dir: str) -> list[ModelInfo]:
    """Recursively scan models_dir for Python files and extract all models."""
    all_models = []
    for root, _dirs, files in os.walk(models_dir):
        for fname in sorted(files):
            if fname.endswith(".py") and not fname.startswith("_"):
                path = os.path.join(root, fname)
                all_models.extend(_parse_model_file(path))
    return all_models


# ---------------------------------------------------------------------------
# PUML generation
# ---------------------------------------------------------------------------

def _generate_puml(models: list[ModelInfo]) -> str:
    model_names = {m.class_name for m in models}

    lines = [
        "@startuml models",
        "' Auto-generated from SQLAlchemy model files.",
        "' Do not edit manually — re-run gen_puml_models.py instead.",
        "",
        "skinparam class {",
        "  BackgroundColor #F5FFF5",
        "  BorderColor #2E7D32",
        "  FontName Monospaced",
        "}",
        "skinparam linetype ortho",
        "",
    ]

    # Emit class blocks
    for model in sorted(models, key=lambda m: m.class_name):
        table_note = f" -- table: {model.table_name}" if model.table_name else ""
        lines.append(f"class {model.class_name}  {{\n{table_note} ")

        for col in model.columns:
            pk_marker = "<<PK>> " if col.primary_key else ""
            fk_marker = "<<FK>> " if col.fk_target else ""
            null_marker = "" if col.nullable else " {NOT NULL}"
            lines.append(
                f"  + {pk_marker}{fk_marker}{col.name} : {col.col_type}{null_marker}"
            )

        if model.relationships:
            lines.append("  --")
            for rel in model.relationships:
                rel_type = "list" if rel.is_list else "ref"
                lines.append(f"  # {rel.attr_name} : {rel.target_class} [{rel_type}]")

        lines.append("}")
        lines.append("")

    # Emit Python inheritance arrows
    lines.append("' --- Inheritance ---")
    for model in models:
        for parent in model.parent_classes:
            if parent in model_names and parent != model.class_name:
                lines.append(f"{parent} <|-- {model.class_name}")
    lines.append("")

    # Emit relationship arrows (only emit one direction to avoid duplicates)
    lines.append("' --- Associations (from relationship() declarations) ---")
    emitted = set()
    for model in models:
        for rel in model.relationships:
            if rel.target_class not in model_names:
                continue
            # Canonical key: smaller name first to deduplicate bidirectional rels
            key = tuple(sorted([model.class_name, rel.target_class]))
            if key in emitted:
                continue
            emitted.add(key)

            if rel.is_list:
                # one model has many rel.target_class
                arrow = f"{model.class_name} \"1\" o-- \"*\" {rel.target_class}"
            else:
                # scalar ref: many-to-one or one-to-one
                arrow = f"{model.class_name} \"*\" o-- \"1\" {rel.target_class}"
            lines.append(f"{arrow} : {rel.attr_name}")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    models_dir = sys.argv[1] if len(sys.argv) > 1 else "server/app/models"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "diagrams/models.puml"

    if not os.path.isdir(models_dir):
        print(f"ERROR: models_dir '{models_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    models = _collect_models(models_dir)

    if not models:
        print("WARNING: No models found. Check models_dir path.", file=sys.stderr)

    puml = _generate_puml(models)

    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(puml)

    print(f"Generated {len(models)} model(s) -> {output_file}")


if __name__ == "__main__":
    main()
