"""FastAPI application for RepoScraper - Code Architecture Search Tool."""

from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.config import settings

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"
from app.database import init_db, get_db, Repository, ArchitectureTag
from app.schemas import (
    RepositoryResponse,
    GitHubSearchParams,
    SearchQuery,
    SearchResult,
    AnalysisResult
)
from app.services.github_service import github_service
from app.services.analysis_service import analysis_service

# Initialize FastAPI app
app = FastAPI(
    title="RepoScraper",
    description="Code Architecture Search Tool - Find repositories by architectural patterns",
    version="0.1.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the frontend dashboard."""
    return FileResponse(STATIC_DIR / "index.html")


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


# --- Health Check ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME}


@app.get("/api/debug/config")
async def debug_config():
    """Debug endpoint to check if environment variables are configured."""
    return {
        "openai_configured": bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10),
        "github_configured": bool(settings.GITHUB_TOKEN and len(settings.GITHUB_TOKEN) > 10),
        "openai_key_prefix": settings.OPENAI_API_KEY[:8] + "..." if settings.OPENAI_API_KEY else "NOT SET",
        "github_key_prefix": settings.GITHUB_TOKEN[:8] + "..." if settings.GITHUB_TOKEN else "NOT SET",
        "model": settings.OPENAI_MODEL,
    }


# --- GitHub Endpoints ---

@app.get("/api/github/search")
async def search_github(
    language: Optional[str] = None,
    min_stars: int = Query(default=100, ge=0),
    max_results: int = Query(default=20, ge=1, le=100),
    query: Optional[str] = None
):
    """
    Search GitHub for repositories matching criteria.
    Does not persist to database - use /api/repos/ingest for that.
    """
    repos = github_service.search_repositories(
        language=language,
        min_stars=min_stars,
        max_results=max_results,
        query=query
    )
    return {"count": len(repos), "repositories": repos}


@app.get("/api/github/repo/{owner}/{repo}")
async def get_github_repo(owner: str, repo: str):
    """Get a specific repository from GitHub."""
    full_name = f"{owner}/{repo}"
    repo_data = github_service.get_repository(full_name)
    
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return repo_data


# --- Repository Ingestion & Analysis ---

@app.post("/api/repos/ingest/{owner}/{repo}", response_model=RepositoryResponse)
async def ingest_repository(
    owner: str,
    repo: str,
    analyze: bool = Query(default=True, description="Run GPT-5 analysis after ingestion"),
    db: Session = Depends(get_db)
):
    """
    Ingest a repository from GitHub into the database and optionally analyze it.
    """
    full_name = f"{owner}/{repo}"
    
    # Check if already exists
    existing = db.query(Repository).filter(Repository.full_name == full_name).first()
    if existing:
        return existing
    
    # Fetch from GitHub
    repo_data = github_service.get_repository(full_name)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found on GitHub")
    
    # Get README
    readme = github_service.get_readme_content(full_name)
    
    # Create repository record
    db_repo = Repository(
        name=repo_data["name"],
        full_name=repo_data["full_name"],
        url=repo_data["url"],
        language=repo_data["language"],
        stars=repo_data["stars"],
        description=repo_data["description"],
        readme_content=readme
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    
    # Run analysis if requested
    if analyze and readme:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured on server")
        
        file_tree = github_service.get_file_tree(full_name)
        try:
            analysis = analysis_service.analyze_architecture(readme, full_name, file_tree)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        
        # Store architecture tags
        for pattern in analysis.architectural_patterns:
            tag = ArchitectureTag(
                repo_id=db_repo.id,
                tag=pattern["name"],
                tag_type="architectural_pattern",
                confidence_score=pattern["confidence"],
                detection_method="gpt5"
            )
            db.add(tag)
        
        for pattern in analysis.design_patterns:
            tag = ArchitectureTag(
                repo_id=db_repo.id,
                tag=pattern["name"],
                tag_type="design_pattern",
                confidence_score=pattern["confidence"],
                detection_method="gpt5"
            )
            db.add(tag)
        
        for infra in analysis.infrastructure:
            tag = ArchitectureTag(
                repo_id=db_repo.id,
                tag=infra["approach"],
                tag_type="infrastructure",
                confidence_score=infra["confidence"],
                detection_method="gpt5"
            )
            db.add(tag)
        
        for framework in analysis.frameworks:
            tag = ArchitectureTag(
                repo_id=db_repo.id,
                tag=framework,
                tag_type="framework",
                confidence_score=1.0,
                detection_method="gpt5"
            )
            db.add(tag)
        
        db.commit()
        db.refresh(db_repo)
    
    return db_repo


@app.post("/api/repos/analyze/{repo_id}", response_model=AnalysisResult)
async def analyze_repository(
    repo_id: int,
    db: Session = Depends(get_db)
):
    """Re-analyze an existing repository with GPT-5."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if not repo.readme_content:
        raise HTTPException(status_code=400, detail="Repository has no README content")
    
    file_tree = github_service.get_file_tree(repo.full_name)
    analysis = analysis_service.analyze_architecture(
        repo.readme_content,
        repo.full_name,
        file_tree
    )
    
    return analysis


# --- Search & Query ---

@app.get("/api/repos", response_model=list[RepositoryResponse])
async def list_repositories(
    language: Optional[str] = None,
    min_stars: int = 0,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List all indexed repositories with optional filters."""
    query = db.query(Repository)
    
    if language:
        query = query.filter(Repository.language.ilike(f"%{language}%"))
    
    if min_stars > 0:
        query = query.filter(Repository.stars >= min_stars)
    
    repos = query.order_by(Repository.stars.desc()).limit(limit).all()
    return repos


@app.get("/api/repos/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: int, db: Session = Depends(get_db)):
    """Get a specific repository by ID."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@app.get("/api/search")
async def search_by_architecture(
    query: str = Query(..., description="Search query like 'microservices python'"),
    min_confidence: float = Query(default=0.5, ge=0, le=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search repositories by architectural patterns.
    Query can include pattern names, languages, or frameworks.
    """
    # Parse query terms
    terms = query.lower().split()
    
    # Search in architecture tags
    results = []
    repos = db.query(Repository).all()
    
    for repo in repos:
        score = 0.0
        matched_tags = []
        
        # Check architecture tags
        for tag in repo.architecture_tags:
            if tag.confidence_score < min_confidence:
                continue
            
            tag_lower = tag.tag.lower()
            for term in terms:
                if term in tag_lower or tag_lower in term:
                    score += tag.confidence_score
                    matched_tags.append(tag.tag)
        
        # Check language
        if repo.language and repo.language.lower() in terms:
            score += 0.5
        
        # Check description
        if repo.description:
            desc_lower = repo.description.lower()
            for term in terms:
                if term in desc_lower:
                    score += 0.2
        
        if score > 0:
            results.append({
                "repository": repo,
                "relevance_score": score,
                "matched_tags": matched_tags
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return results[:limit]


@app.get("/api/tags")
async def list_tags(
    tag_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all unique architecture tags in the database."""
    query = db.query(ArchitectureTag)
    
    if tag_type:
        query = query.filter(ArchitectureTag.tag_type == tag_type)
    
    tags = query.all()
    
    # Aggregate tags
    tag_counts = {}
    for tag in tags:
        key = (tag.tag, tag.tag_type)
        if key not in tag_counts:
            tag_counts[key] = {"tag": tag.tag, "type": tag.tag_type, "count": 0, "avg_confidence": 0}
        tag_counts[key]["count"] += 1
        tag_counts[key]["avg_confidence"] += tag.confidence_score
    
    # Calculate averages
    for key in tag_counts:
        tag_counts[key]["avg_confidence"] /= tag_counts[key]["count"]
    
    return list(tag_counts.values())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
