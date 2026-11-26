import logging
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _normalize_url(url: str) -> str:
    """Make common provider URLs work with the drivers we install.

    Render/Heroku hand out ``postgres://`` or ``postgresql://`` URLs, but
    SQLAlchemy needs the driver name in the scheme. Without this, SQLAlchemy
    looks for psycopg2 (which is not installed) and the app crashes on boot.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _engine_options(url: str) -> dict:
    options: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
    elif url.startswith("postgresql"):
        # Do not let a dead/expired database hang startup forever.
        options["connect_args"] = {"connect_timeout": 5}
    elif url.startswith("mysql"):
        options["connect_args"] = {"connect_timeout": 5}
    return options


DATABASE_URL = _normalize_url(settings.DATABASE_URL)
engine = create_engine(DATABASE_URL, **_engine_options(DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# "primary" or "fallback" — surfaced by /api/health so this is never silent.
_db_mode = "primary"


def _safe_target(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return url
    return f"{parsed.scheme}://{parsed.hostname or ''}{parsed.path or ''}"


def _switch_to_fallback() -> None:
    global engine, SessionLocal, _db_mode
    fallback_url = _normalize_url(settings.SQLITE_FALLBACK_URL)
    logger.warning(
        "Primary database is unavailable. Falling back to %s. "
        "Accounts created in fallback mode are lost when the service restarts.",
        _safe_target(fallback_url),
    )
    try:
        engine.dispose()
    except Exception:
        pass
    engine = create_engine(fallback_url, **_engine_options(fallback_url))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    _db_mode = "fallback"


def init_db() -> None:
    """Create tables, with a bounded attempt against the primary database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database ready: %s", _safe_target(DATABASE_URL))
        return
    except Exception as exc:  # noqa: BLE001 - startup must not crash-loop
        logger.error(
            "Could not initialize database %s: %s",
            _safe_target(DATABASE_URL),
            exc,
        )
        if not settings.ALLOW_SQLITE_FALLBACK or DATABASE_URL.startswith("sqlite"):
            raise
        _switch_to_fallback()


def database_status() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        connected = True
    except Exception:
        connected = False
    return {"mode": _db_mode, "connected": connected}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
