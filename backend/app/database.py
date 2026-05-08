from sqlmodel import create_engine, Session
from .config import settings
from sqlmodel import SQLModel
import os
from contextlib import contextmanager
from fastapi import HTTPException, status
from .utils.logging_util import log_operation, log_error

DATABASE_URL = settings.DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    connect_args["timeout"] = 30

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

log_operation("database_init", {
    "database_url": DATABASE_URL,
    "engine_created": True
}, "info")

def init_db():
    """Initialize the database - only create tables that don't exist"""
    try:
        from .models import metadata_init
        metadata_init()
        from .utils.logging_util import log_database_operation

        log_operation("database_init_start", {
            "message": "Starting database initialization"
        }, "info")

        from sqlmodel import SQLModel
        from sqlalchemy import inspect

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        for table in SQLModel.metadata.sorted_tables:
            if table.name not in existing_tables:
                table.create(engine)
                log_database_operation("create", table.name, None, None, True, None)
            else:
                log_database_operation("exists", table.name, None, None, True, f"Table {table.name} already exists, skipping creation.")

        log_operation("database_init_complete", {
            "message": "Database initialization completed successfully"
        }, "info")

    except Exception as e:
        log_error("database_init", e, None, {"database_url": DATABASE_URL})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}"
        )

@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

from fastapi import Depends

def get_session_context():
    with get_session() as session:
        yield session
