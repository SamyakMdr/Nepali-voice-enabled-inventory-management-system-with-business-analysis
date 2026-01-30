import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Get DB URL from .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Create Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Class
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()