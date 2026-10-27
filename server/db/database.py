"""
Database engine, session factory, and dependency injection for FastAPI.

Uses SQLAlchemy 2.x with a declarative base. SQLite connections are configured
with ``check_same_thread=False`` so they can be shared across FastAPI's async
workers.
"""

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server.config import settings


# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------

connect_args: dict[str, Any] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables and apply safe non-destructive schema migrations."""
    # Ensure models are imported before creating tables
    import server.db.models  # noqa: F401
    from sqlalchemy import inspect, text

    Base.metadata.create_all(bind=engine)

    # Safe column migrations for SQLite
    try:
        inspector = inspect(engine)
        if "alerts" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("alerts")}
            with engine.connect() as conn:
                if "source_tier" not in columns:
                    conn.execute(text("ALTER TABLE alerts ADD COLUMN source_tier VARCHAR(20) DEFAULT 'unverified'"))
                    conn.commit()
                if "parent_alert_id" not in columns:
                    conn.execute(text("ALTER TABLE alerts ADD COLUMN parent_alert_id INTEGER REFERENCES alerts(id)"))
                    conn.commit()
                if "secondary_categories" not in columns:
                    conn.execute(text("ALTER TABLE alerts ADD COLUMN secondary_categories TEXT"))
                    conn.commit()
    except Exception as e:
        import logging
        logging.getLogger("database").warning(f"Schema migration warning: {e}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    The session is automatically closed when the request finishes.

    Yields:
        A SQLAlchemy ``Session`` bound to the configured engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
