from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- Create database engine (creates careershield.db file) ---
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
engine = create_engine(f'sqlite:///{BASE_DIR}/careershield.db')

# --- Base class for all tables ---
Base = declarative_base()

# --- Table 1: Users ---
class User(Base):
    __tablename__ = 'users'
    id       = Column(Integer, primary_key=True)      # unique user id
    username = Column(String, unique=True)             # unique username
    email    = Column(String, unique=True)             # unique email
    password = Column(String)                          # hashed password
    created  = Column(DateTime, default=datetime.now)  # account creation time

# --- Table 2: Resume History ---
class ResumeHistory(Base):
    __tablename__ = 'resume_history'
    id         = Column(Integer, primary_key=True)     # unique record id
    user_id    = Column(Integer)                       # which user uploaded
    filename   = Column(String)                        # resume file name
    skills     = Column(Text)                          # extracted skills
    ats_score  = Column(Float)                         # ATS score out of 100
    qual_score = Column(Float)                         # quality score out of 100
    category   = Column(String)                        # predicted job category
    created    = Column(DateTime, default=datetime.now) # upload time

# --- Table 3: Job Analysis History ---
class JobAnalysis(Base):
    __tablename__ = 'job_analysis'
    id            = Column(Integer, primary_key=True)  # unique record id
    user_id       = Column(Integer)                    # which user analysed
    job_title     = Column(String)                     # job title
    fraud_score   = Column(Float)                      # fraud probability
    fraud_reasons = Column(Text)                       # SHAP explanation
    match_score   = Column(Float)                      # resume match %
    created       = Column(DateTime, default=datetime.now) # analysis time

# --- Table 4: Reports ---
class Report(Base):
    __tablename__ = 'reports'
    id          = Column(Integer, primary_key=True)    # unique record id
    user_id     = Column(Integer)                      # which user
    report_path = Column(String)                       # path to PDF file
    created     = Column(DateTime, default=datetime.now) # report time

# --- Create all tables in the database ---
Base.metadata.create_all(engine)

# --- Session maker (used to query database) ---
SessionLocal = sessionmaker(bind=engine)

print("Database and tables created successfully!")