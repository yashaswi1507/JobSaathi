"""
database.py — Database Configuration
SQLite locally, PostgreSQL on Render/production
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Auto-detect: PostgreSQL on Render, SQLite locally
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # PostgreSQL (Render) — fix postgres:// to postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
    print(f"[DB] Using PostgreSQL ✅")
else:
    # SQLite (local development)
    engine = create_engine(
        "sqlite:///./jobsaathi.db",
        connect_args={"check_same_thread": False}
    )
    print("[DB] Using SQLite (local) ✅")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email    = Column(String, unique=True, index=True)
    password = Column(String)
    created  = Column(DateTime, default=datetime.utcnow)

class ResumeHistory(Base):
    __tablename__ = "resume_history"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, index=True)
    filename      = Column(String)
    ats_score     = Column(Float, default=0)
    quality_score = Column(Float, default=0)
    skills        = Column(Text, default="[]")
    created_at    = Column(DateTime, default=datetime.utcnow)

class JobAnalysis(Base):
    __tablename__ = "job_analysis"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, index=True)
    job_title   = Column(String)
    fraud_score = Column(Float, default=0)
    verdict     = Column(String)
    created_at  = Column(DateTime, default=datetime.utcnow)

# Create all tables
Base.metadata.create_all(bind=engine)
print("[DB] Tables created/verified ✅")
