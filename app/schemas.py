"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# --- Repository Schemas ---

class ArchitectureTagBase(BaseModel):
    tag: str
    tag_type: Optional[str] = None
    confidence_score: float = 0.0
    detection_method: str = "gpt5"


class ArchitectureTagResponse(ArchitectureTagBase):
    id: int
    repo_id: int

    class Config:
        from_attributes = True


class RepositoryBase(BaseModel):
    name: str
    full_name: str
    url: str
    language: Optional[str] = None
    stars: int = 0
    description: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    readme_content: Optional[str] = None


class RepositoryResponse(RepositoryBase):
    id: int
    last_indexed: datetime
    architecture_tags: list[ArchitectureTagResponse] = []

    class Config:
        from_attributes = True


# --- Search Schemas ---

class SearchQuery(BaseModel):
    query: str  # Natural language query like "Python microservices with event-driven"
    language: Optional[str] = None
    min_stars: int = 0
    limit: int = 20


class SearchResult(BaseModel):
    repository: RepositoryResponse
    relevance_score: float


# --- GitHub Search Schemas ---

class GitHubSearchParams(BaseModel):
    language: Optional[str] = None
    min_stars: int = 100
    max_results: int = 50
    query: Optional[str] = None  # Additional search terms


# --- Analysis Schemas ---

class AnalysisResult(BaseModel):
    architectural_patterns: list[dict]  # [{"name": "...", "confidence": 0.0-1.0}]
    design_patterns: list[dict]
    infrastructure: list[dict]
    frameworks: list[str]
    summary: str
