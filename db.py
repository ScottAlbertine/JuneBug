from contextlib import contextmanager
from typing import Generator

from peewee import SqliteDatabase

from annotations import ProjectPath
from db_models import ALL_MODELS

databases: dict[str, SqliteDatabase] = {}


@contextmanager
def get_db(project_path: ProjectPath) -> Generator[SqliteDatabase, None, None]:
    """
    Get a DB cursor that can be used to query data for the given project path.
    All data is sharded by project path.
    All data is stored in memory, which disappears when the server exits.
    This is to match the behavior where all debugees exit when the server exits.
    The cursor is already in a transaction, and will attempt to commit when this context manager exits.
    The DB tables have already been created for you.
    """
    if project_path in databases:
        db = databases[project_path]
    else:
        # only create the DB, and its tables, if we haven't already done so
        db = SqliteDatabase(":memory:")
        with db.bind_ctx(ALL_MODELS):
            db.create_tables(ALL_MODELS)
        databases[project_path] = db

    with db.bind_ctx(ALL_MODELS):
        yield db
