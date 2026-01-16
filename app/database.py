"""Database configuration and models for RepoScraper."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "sqlite:///./reposcraper.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Repository(Base):
    """Repository metadata table."""
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), unique=True, nullable=False)  # owner/repo
    url = Column(String(1024), nullable=False)
    language = Column(String(100))
    stars = Column(Integer, default=0)
    description = Column(Text)
    readme_content = Column(Text)
    last_indexed = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to architecture tags
    architecture_tags = relationship("ArchitectureTag", back_populates="repository", cascade="all, delete-orphan")


class ArchitectureTag(Base):
    """Architecture tags detected for repositories."""
    __tablename__ = "architecture_tags"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    tag = Column(String(255), nullable=False)
    tag_type = Column(String(100))  # architectural_pattern, design_pattern, infrastructure, framework
    confidence_score = Column(Float, default=0.0)
    detection_method = Column(String(100), default="gpt5")  # gpt5, heuristic, manual
    
    # Relationship back to repository
    repository = relationship("Repository", back_populates="architecture_tags")


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
