"""
app/core/database.py

Sets up the connection to Postgres using SQLAlchemy.
Every module (auth, exams, questions, etc.) imports `Base` to define
its models, and `get_db` to get a database session inside a route.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# The "engine" is the actual connection pool to Postgres
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Each request gets its own short-lived session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All models (User, Organization, Exam, Question, etc.) inherit from this
Base = declarative_base()


def get_db():
    """
    FastAPI dependency. Use it in routes like:

        @router.get("/something")
        def endpoint(db: Session = Depends(get_db)):
            ...

    It opens a DB session, hands it to the route, and always closes it
    afterward — even if the route raises an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
