from sqlalchemy import create_engine
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


def init_db() -> None:
    """Create missing tables. Production would use Alembic migrations."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
