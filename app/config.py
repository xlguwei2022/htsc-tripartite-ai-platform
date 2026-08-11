import os
from pathlib import Path

APP_NAME = "华泰证券三方协议智能运营中台 Runtime PoC"
APP_VERSION = "1.5.0-public"
HOST = os.getenv("TRIPARTITE_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("TRIPARTITE_PORT", "8013")))
DEMO_BASE_DATE = os.getenv("DEMO_BASE_DATE", "2026-08-10")
APP_ENV = os.getenv("APP_ENV", "local")

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PATH = ROOT / "frontend" / "index.html"
DATA_DIR = Path(os.getenv("TRIPARTITE_DATA_DIR", str(ROOT / "data")))
DB_PATH = DATA_DIR / "tripartite_poc.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Render and some providers may expose the legacy postgres:// scheme.
# SQLAlchemy expects postgresql://.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

DATABASE_KIND = "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite"
