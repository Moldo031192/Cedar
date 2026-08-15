import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required and was not set. "
        "No default host/port is assumed, because the correct value differs "
        "between Full Docker (db:5432) and Hybrid development (127.0.0.1:5433). "
        "See backend/.env.example."
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()