"""
database.py — Database engine, session factory, and Base declarative class.

Uses DATABASE_URL from .env via python-dotenv.
Creates all tables on import if they don't exist (hackathon speed — no migrations).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wyibe.db")

# For SQLite, check_same_thread allows FastAPI dependency injection.
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency — yields a DB session, auto-closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables. Called on app startup."""
    Base.metadata.create_all(bind=engine)
