import os


def _database_uri():
    """Resolve the database URL, avoiding ephemeral SQLite on Vercel."""
    database_url = (os.environ.get("DATABASE_URL") or "").strip()

    if not database_url:
        if os.environ.get("VERCEL"):
            raise RuntimeError(
                "DATABASE_URL is required on Vercel. Add your Neon PostgreSQL "
                "connection string in Project Settings > Environment Variables."
            )
        return "sqlite:///wafyurl.db"

    # Some providers still supply the legacy postgres:// scheme.
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]

    # Ensure SQLAlchemy uses the installed psycopg2 driver explicitly.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgresql://"):]

    return database_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PUBLIC_BASE_URL = (os.environ.get("PUBLIC_BASE_URL") or "https://url.amwafy.xyz").rstrip("/")

    if SQLALCHEMY_DATABASE_URI.startswith(("postgresql://", "postgresql+psycopg2://")):
        # Keep per-instance connection usage modest in serverless environments.
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 1,
            "max_overflow": 0,
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
