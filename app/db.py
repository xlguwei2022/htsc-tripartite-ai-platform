import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATA_DIR, DATABASE_KIND, DATABASE_URL

if DATABASE_KIND == "SQLite":
    DATA_DIR.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for the Runtime PoC."""


engine_kwargs = {"future": True, "pool_pre_ping": True}
if DATABASE_KIND == "SQLite":
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db(max_attempts: int = 8, base_delay_seconds: float = 1.0) -> None:
    """Create missing tables with bounded retry for cloud database readiness.

    Render may start the web service while a newly-created Postgres instance is
    still becoming reachable. Retrying here keeps the first deploy deterministic
    without hiding persistent configuration errors.
    """
    from . import models  # noqa: F401

    for attempt in range(1, max_attempts + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            engine.dispose()
            if attempt >= max_attempts:
                raise
            delay = min(base_delay_seconds * (2 ** (attempt - 1)), 8.0)
            time.sleep(delay)
