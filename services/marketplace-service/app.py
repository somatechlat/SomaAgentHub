"""
Capsule Marketplace Service
Package management and distribution for Task Capsules.

Enables discovery, installation, versioning, and ratings for reusable capsules.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib
import json
import logging
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://somagent:somagent@localhost:5432/somagent")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class CapsulePackage(Base):
    """Capsule package database model."""
    __tablename__ = "capsule_packages"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    version = Column(String, nullable=False)
    description = Column(Text)
    author = Column(String, nullable=False)
    category = Column(String, index=True)
    tags = Column(JSON)  # List of tags
    dependencies = Column(JSON)  # {"package-name": "^1.0.0"}
    capsule_data = Column(JSON, nullable=False)  # Complete capsule definition
    signature = Column(String)  # Cryptographic signature
    downloads = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CapsuleRating(Base):
    """Capsule rating database model."""
    __tablename__ = "capsule_ratings"
    
    id = Column(String, primary_key=True)
    package_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CapsuleCreate(BaseModel):
    """Request model for creating a capsule package."""
    name: str = Field(..., description="Package name (unique)")
    version: str = Field(..., description="Semantic version (e.g., 1.0.0)")
    description: str = Field(..., description="Package description")
    author: str = Field(..., description="Author name/email")
    category: str = Field(..., description="Category (analytics, security, devops, etc.)")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Package dependencies")
    capsule_data: Dict[str, Any] = Field(..., description="Complete capsule definition")


class CapsuleResponse(BaseModel):
    """Response model for capsule package."""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    dependencies: Dict[str, str]
    signature: Optional[str]
    downloads: int
    rating_average: float
    rating_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    """Request model for creating a rating."""
    package_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    review: Optional[str] = Field(None, description="Optional review text")


class SearchQuery(BaseModel):
    """Search query model."""
    query: Optional[str] = Field(None, description="Search text")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    limit: int = Field(25, le=100)


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Capsule Marketplace",
    description="Task Capsule package management and distribution",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/packages", response_model=CapsuleResponse)
def publish_package(capsule: CapsuleCreate, db: Session = Depends(get_db)):
    """Publish a new capsule package to the marketplace."""
    # Check if package already exists
    existing = db.query(CapsulePackage).filter(CapsulePackage.name == capsule.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Package '{capsule.name}' already exists")
    
    # Generate ID and signature
    package_id = hashlib.sha256(f"{capsule.name}:{capsule.version}".encode()).hexdigest()[:16]
    signature = hashlib.sha256(json.dumps(capsule.capsule_data, sort_keys=True).encode()).hexdigest()
    
    # Create package
    package = CapsulePackage(
        id=package_id,
        name=capsule.name,
        version=capsule.version,
        description=capsule.description,
        author=capsule.author,
        category=capsule.category,
        tags=capsule.tags,
        dependencies=capsule.dependencies,
        capsule_data=capsule.capsule_data,
        signature=signature
    )
    
    db.add(package)
    db.commit()
    db.refresh(package)
    
    logger.info(f"Published package: {capsule.name} v{capsule.version}")
    return package


@app.get("/packages/{package_name}", response_model=CapsuleResponse)
def get_package(package_name: str, db: Session = Depends(get_db)):
    """Get package by name (latest version)."""
    package = db.query(CapsulePackage).filter(CapsulePackage.name == package_name).first()
    if not package:
        raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found")
    return package


@app.get("/packages/{package_name}/download")
def download_package(package_name: str, db: Session = Depends(get_db)):
    """Download package capsule data and increment download counter."""
    package = db.query(CapsulePackage).filter(CapsulePackage.name == package_name).first()
    if not package:
        raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found")
    
    # Increment downloads
    package.downloads += 1
    db.commit()
    
    logger.info(f"Downloaded package: {package_name} (total: {package.downloads})")
    
    return {
        "name": package.name,
        "version": package.version,
        "capsule": package.capsule_data,
        "signature": package.signature,
        "dependencies": package.dependencies
    }


@app.post("/packages/search", response_model=List[CapsuleResponse])
def search_packages(query: SearchQuery, db: Session = Depends(get_db)):
    """Search packages with filters."""
    q = db.query(CapsulePackage)
    
    # Text search in name/description
    if query.query:
        search = f"%{query.query}%"
        q = q.filter(
            (CapsulePackage.name.ilike(search)) | 
            (CapsulePackage.description.ilike(search))
        )
    
    # Category filter
    if query.category:
        q = q.filter(CapsulePackage.category == query.category)
    
    # Tags filter (any tag match)
    if query.tags:
        # PostgreSQL JSON contains
        for tag in query.tags:
            q = q.filter(CapsulePackage.tags.contains([tag]))
    
    # Rating filter
    if query.min_rating is not None:
        q = q.filter(CapsulePackage.rating_average >= query.min_rating)
    
    # Order by popularity
    q = q.order_by(CapsulePackage.downloads.desc())
    
    # Limit
    packages = q.limit(query.limit).all()
    
    logger.info(f"Search returned {len(packages)} packages")
    return packages


@app.post("/ratings")
def create_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    """Create or update a rating for a package."""
    # Get package
    package = db.query(CapsulePackage).filter(CapsulePackage.id == rating.package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Create rating
    rating_id = hashlib.sha256(f"{rating.package_id}:{rating.user_id}".encode()).hexdigest()[:16]
    rating_obj = CapsuleRating(
        id=rating_id,
        package_id=rating.package_id,
        user_id=rating.user_id,
        rating=rating.rating,
        review=rating.review
    )
    
    db.add(rating_obj)
    
    # Update package rating average
    all_ratings = db.query(CapsuleRating).filter(CapsuleRating.package_id == rating.package_id).all()
    avg_rating = sum(r.rating for r in all_ratings) / len(all_ratings)
    package.rating_average = avg_rating
    package.rating_count = len(all_ratings)
    
    db.commit()
    
    logger.info(f"Created rating for {package.name}: {rating.rating} stars")
    
    return {"message": "Rating created", "average": avg_rating}


@app.get("/packages/{package_name}/ratings")
def get_package_ratings(package_name: str, db: Session = Depends(get_db)):
    """Get all ratings for a package."""
    package = db.query(CapsulePackage).filter(CapsulePackage.name == package_name).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    ratings = db.query(CapsuleRating).filter(CapsuleRating.package_id == package.id).all()
    
    return {
        "package": package_name,
        "average": package.rating_average,
        "count": package.rating_count,
        "ratings": [
            {
                "user_id": r.user_id,
                "rating": r.rating,
                "review": r.review,
                "created_at": r.created_at
            }
            for r in ratings
        ]
    }


@app.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """List all categories with package counts."""
    from sqlalchemy import func
    
    categories = db.query(
        CapsulePackage.category,
        func.count(CapsulePackage.id).label("count")
    ).group_by(CapsulePackage.category).all()
    
    return [{"name": cat, "count": count} for cat, count in categories]


@app.get("/popular", response_model=List[CapsuleResponse])
def get_popular_packages(limit: int = 10, db: Session = Depends(get_db)):
    """Get most popular packages by download count."""
    packages = db.query(CapsulePackage).order_by(
        CapsulePackage.downloads.desc()
    ).limit(limit).all()
    
    return packages


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "capsule-marketplace"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)
