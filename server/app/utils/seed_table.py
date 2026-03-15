import os
import json
from typing import Type
from server.extensions import db

def seed_table(
        model: Type[db.Model],
        seeds_file : str,
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

    if not os.path.exists(seeds_file):
        print(f"[{model.__tablename__}] seed file not found: {seeds_file}")
        return

    with open(seeds_file, encoding="utf-8") as f:
        data = json.load(f)

    added = 0
    skipped = 0

    for item in data:
        if skip_duplicates:
            filters = {field: item[field] for field in unique_fields}
            exists = model.query.filter_by(**filters).first()
            if exists:
                skipped += 1
                continue

        db.session.add(model(**item))
        added += 1

    db.session.commit()
    print("Commit done.")

    if verbose:
        print(f"[{model.__tablename__}] added: {added}, skipped: {skipped}")
