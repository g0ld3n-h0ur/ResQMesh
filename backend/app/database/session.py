"""
app/database/session.py

SQLAlchemy session factory and FastAPI dependency for database access.

Usage in a route:
    @router.get("/example")
    def example(db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.database.database import engine

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and ensure it is closed after the request.

    This is the standard FastAPI dependency for injecting DB sessions
    into route handlers and services.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
