"""
Database connection layer.

Default:  SQLite (file-based, zero setup)
          → storage/aireviewbot.db

Production: Set DATABASE_URL in .env to a PostgreSQL DSN, e.g.
            postgresql+psycopg2://user:pass@host/dbname
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # cheap health-check before each connection use
)

# Enable WAL mode for SQLite so reads don't block writes
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_wal_mode(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA journal_mode=WAL")


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base class for ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db():
    """FastAPI dependency: yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (idempotent – safe to call on every startup)."""
    # Import models so SQLAlchemy sees their metadata before creating tables.
    from backend.app.db import models  # noqa: F401

    # Ensure the storage directory exists when using SQLite
    if _is_sqlite:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    Base.metadata.create_all(bind=engine)
