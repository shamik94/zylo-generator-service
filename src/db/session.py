# backend/db/session.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from src.db.base import Base  # Import Base from base.py
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Define your connection URL
#    In a real project, you'd likely read from environment variables.
#    For Docker Compose on port 5433, use something like:
#       postgresql+psycopg2://user:password@localhost:5433/email_generator

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Handle Heroku's DATABASE_URL format
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Create the Engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True
)  # echo=True logs SQL to console (for debugging)

# 3. Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 4. (Optional) If using FastAPI, you can provide a dependency that yields DB sessions:
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
