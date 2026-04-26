import json
from pathlib import Path
from typing import Type
from server.extensions import db
from sqlalchemy import inspect

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_seed_path(seeds_file: str) -> Path:
    candidate = Path(seeds_file)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def seed_table(
        model: Type[db.Model],
        seeds_file: str,
        unique_fields: list[str],
        skip_duplicates: bool = True,
        verbose: bool = True
    ) -> None:
    """
    :param model: SQLAlchemy model (e.g., PageText, User)
    :param seeds_file: path to a JSON file containing data
    :param unique_fields: fields to check for duplicates (e.g., [“page”, ‘key’, “language”])
    :param skip_duplicates: skip if the record already exists (default: True)
    :param verbose: output a log (default: True)
    :return: None
    """
    """
    print(f"CWD: {os.getcwd()}")                          # Where is it launched from?
    print(f"Looking for: {os.path.abspath(seeds_file)}")  # full path to the file
    print(f"Exists: {os.path.exists(seeds_file)}")        # Does the file exist?
    """

    resolved_path = _resolve_seed_path(seeds_file)

    if not resolved_path.exists():
        print(f"[{model.__tablename__}] seed file not found: {seeds_file}")
        return

    with open(resolved_path, encoding="utf-8") as f:
        data = json.load(f)

    added = 0
    skipped = 0

    # get information about the model's columns
    mapper = inspect(model)
    columns = {col.key: col for col in mapper.columns}

    for item in data:
        if skip_duplicates:
            filters = {field: item[field] for field in unique_fields}
            exists = model.query.filter_by(**filters).first()
            if exists:
                skipped += 1
                continue

        # Forming a dict taking into account defaults
        model_data = {}

        for key, column in columns.items():
            if key in item:
                value = item[key]

                # if the value None is default, skip the field
                if value is None and (column.default is not None or column.server_default is not None):
                    continue

                model_data[key] = value
            else:
                # if there is no key, we don't pass it, SQLAlchemy will use default
                continue

        for rel in inspect(model).relationships:
            fk_column = list(rel.local_columns)[0].key

            if fk_column in model_data and model_data[fk_column] is not None:
                target_model = rel.mapper.class_

                exists = db.session.get(target_model, model_data[fk_column])
                if not exists:
                    raise ValueError(
                        f"{model.__name__}: {fk_column}={model_data[fk_column]} "
                        f"does not exist in {target_model.__name__}"
                    )
        db.session.add(model(**model_data))
        added += 1

    db.session.commit()
    print("Commit done.")

    if verbose:
        print(f"[{model.__tablename__}] added: {added}, skipped: {skipped}")
