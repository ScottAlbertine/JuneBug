from contextlib import contextmanager
from hashlib import md5
from typing import Generator

from peewee import SqliteDatabase

from annotations import ProjectPath
from constants import TEMP_DIR
from db_models import ALL_MODELS

databases: dict[str, SqliteDatabase] = {}


@contextmanager
def get_db(project_path: ProjectPath) -> Generator[SqliteDatabase, None, None]:
    """Get a DB cursor that can be used to query data for the given project path.

    The cursor is already in a transaction, and will attempt to commit when this context manager exits.
    The DB tables have already been created for you.
    """
    # hash the project path to get the DB name
    # this shards everything by project path, since every single endpoint specifies it explicitly
    db_file_hash = md5(project_path.encode("utf-8")).hexdigest()
    db_file_path = str(TEMP_DIR / f"JuneBug_{db_file_hash}.db")

    if db_file_path in databases:
        db = databases[db_file_path]
    else:
        # only create the DB, and its tables, if we haven't already done so
        db = SqliteDatabase(db_file_path)
        with db.bind_ctx(ALL_MODELS):
            db.create_tables(ALL_MODELS)
        databases[db_file_path] = db

    with db.bind_ctx(ALL_MODELS):
        yield db
