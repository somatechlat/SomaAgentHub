"""Marketplace API for publishing and discovering task capsules.

Provides CRUD endpoints for capsule marketplace with ratings and download tracking.
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from .db import (
    get_db,
    Capsule,
    CapsuleVersion,
    CapsuleRating,
    CapsuleDownload,
)

app = FastAPI(
    title="SomaGent Marketplace API",
    description="Task capsule marketplace with publishing, discovery, and ratings",
    version="1.0.0",
)


# ============================================================================
# Pydantic Schemas
# ============================================================================


class CapsulePublishRequest(BaseModel):
    """Request to publish a new capsule."""
    
    name: str = Field(..., description="Capsule name")
    description: str = Field(..., description="Capsule description")
    author: str = Field(..., description="Author username")
    category: str = Field(..., description="Category (e.g., 'data-analysis', 'automation')")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    source_url: str = Field(..., description="S3 URL to capsule artifact")
    version: str = Field(default="1.0.0", description="Version string")
    readme: Optional[str] = Field(None, description="Markdown README content")


class CapsuleUpdateRequest(BaseModel):
    """Request to update capsule metadata."""
    
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    readme: Optional[str] = None


class CapsuleRatingRequest(BaseModel):
    """Request to rate a capsule."""
    
    user_id: str = Field(..., description="Rating user ID")
    rating: int = Field(..., ge=1, le=5, description="Star rating (1-5)")
    review: Optional[str] = Field(None, description="Optional review text")


class CapsuleResponse(BaseModel):
    """Capsule listing response."""
    
    id: str
    name: str
    description: str
    author: str
    category: str
    tags: List[str]
    version: str
    downloads: int
    rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CapsuleDetailResponse(CapsuleResponse):
    """Detailed capsule response with README and versions."""
    
    readme: Optional[str] = None
    source_url: str
    versions: List[str] = Field(default_factory=list)


class RatingResponse(BaseModel):
    """Rating response."""
    
    id: str
    user_id: str
    rating: int
    review: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "marketplace"}


@app.post("/v1/capsules", response_model=CapsuleResponse, status_code=201)
async def publish_capsule(
    request: CapsulePublishRequest,
    db: Session = Depends(get_db),
):
    """Publish a new task capsule to the marketplace.
    
    Args:
        request: Capsule publication request
        db: Database session
        
    Returns:
        Created capsule details
    """
    # Create capsule
    capsule = Capsule(
        name=request.name,
        description=request.description,
        author=request.author,
        category=request.category,
        tags=request.tags,
        readme=request.readme,
        source_url=request.source_url,
    )
    db.add(capsule)
    db.flush()
    
    # Create initial version
    version = CapsuleVersion(
        capsule_id=capsule.id,
        version=request.version,
        source_url=request.source_url,
    )
    db.add(version)
    db.commit()
    db.refresh(capsule)
    
    return CapsuleResponse(
        id=capsule.id,
        name=capsule.name,
        description=capsule.description,
        author=capsule.author,
        category=capsule.category,
        tags=capsule.tags,
        version=request.version,
        downloads=0,
        rating=0.0,
        rating_count=0,
        created_at=capsule.created_at,
        updated_at=capsule.updated_at,
    )


@app.get("/v1/capsules", response_model=List[CapsuleResponse])
async def list_capsules(
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """List capsules with optional filters.
    
    Args:
        category: Filter by category
        author: Filter by author
        tags: Comma-separated tag list
        limit: Maximum results
        offset: Pagination offset
        db: Database session
        
    Returns:
        List of capsules
    """
    query = db.query(Capsule)
    
    if category:
        query = query.filter(Capsule.category == category)
    
    if author:
        query = query.filter(Capsule.author == author)
    
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        # Filter capsules that have any of the specified tags
        query = query.filter(Capsule.tags.overlap(tag_list))
    
    capsules = query.order_by(Capsule.created_at.desc()).offset(offset).limit(limit).all()
    
    # Build responses with aggregated stats
    results = []
    for capsule in capsules:
        # Get download count
        download_count = db.query(func.count(CapsuleDownload.id)).filter(
            CapsuleDownload.capsule_id == capsule.id
        ).scalar() or 0
        
        # Get rating stats
        rating_stats = db.query(
            func.avg(CapsuleRating.rating),
            func.count(CapsuleRating.id)
        ).filter(
            CapsuleRating.capsule_id == capsule.id
        ).first()
        
        avg_rating = float(rating_stats[0] or 0.0)
        rating_count = int(rating_stats[1] or 0)
        
        # Get latest version
        latest_version = db.query(CapsuleVersion).filter(
            CapsuleVersion.capsule_id == capsule.id
        ).order_by(CapsuleVersion.created_at.desc()).first()
        
        results.append(CapsuleResponse(
            id=capsule.id,
            name=capsule.name,
            description=capsule.description,
            author=capsule.author,
            category=capsule.category,
            tags=capsule.tags,
            version=latest_version.version if latest_version else "1.0.0",
            downloads=download_count,
            rating=round(avg_rating, 1),
            rating_count=rating_count,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
        ))
    
    return results


@app.get("/v1/capsules/{capsule_id}", response_model=CapsuleDetailResponse)
async def get_capsule(
    capsule_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed capsule information.
    
    Args:
        capsule_id: Capsule UUID
        db: Database session
        
    Returns:
        Detailed capsule info
    """
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    # Get download count
    download_count = db.query(func.count(CapsuleDownload.id)).filter(
        CapsuleDownload.capsule_id == capsule.id
    ).scalar() or 0
    
    # Get rating stats
    rating_stats = db.query(
        func.avg(CapsuleRating.rating),
        func.count(CapsuleRating.id)
    ).filter(
        CapsuleRating.capsule_id == capsule.id
    ).first()
    
    avg_rating = float(rating_stats[0] or 0.0)
    rating_count = int(rating_stats[1] or 0)
    
    # Get all versions
    versions = db.query(CapsuleVersion).filter(
        CapsuleVersion.capsule_id == capsule.id
    ).order_by(CapsuleVersion.created_at.desc()).all()
    
    version_list = [v.version for v in versions]
    latest_version = versions[0] if versions else None
    
    return CapsuleDetailResponse(
        id=capsule.id,
        name=capsule.name,
        description=capsule.description,
        author=capsule.author,
        category=capsule.category,
        tags=capsule.tags,
        readme=capsule.readme,
        source_url=latest_version.source_url if latest_version else capsule.source_url,
        version=latest_version.version if latest_version else "1.0.0",
        versions=version_list,
        downloads=download_count,
        rating=round(avg_rating, 1),
        rating_count=rating_count,
        created_at=capsule.created_at,
        updated_at=capsule.updated_at,
    )


@app.put("/v1/capsules/{capsule_id}", response_model=CapsuleResponse)
async def update_capsule(
    capsule_id: str,
    request: CapsuleUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update capsule metadata.
    
    Args:
        capsule_id: Capsule UUID
        request: Update request
        db: Database session
        
    Returns:
        Updated capsule
    """
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    if request.description is not None:
        capsule.description = request.description
    if request.category is not None:
        capsule.category = request.category
    if request.tags is not None:
        capsule.tags = request.tags
    if request.readme is not None:
        capsule.readme = request.readme
    
    capsule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(capsule)
    
    # Get stats for response
    download_count = db.query(func.count(CapsuleDownload.id)).filter(
        CapsuleDownload.capsule_id == capsule.id
    ).scalar() or 0
    
    rating_stats = db.query(
        func.avg(CapsuleRating.rating),
        func.count(CapsuleRating.id)
    ).filter(
        CapsuleRating.capsule_id == capsule.id
    ).first()
    
    latest_version = db.query(CapsuleVersion).filter(
        CapsuleVersion.capsule_id == capsule.id
    ).order_by(CapsuleVersion.created_at.desc()).first()
    
    return CapsuleResponse(
        id=capsule.id,
        name=capsule.name,
        description=capsule.description,
        author=capsule.author,
        category=capsule.category,
        tags=capsule.tags,
        version=latest_version.version if latest_version else "1.0.0",
        downloads=download_count,
        rating=round(float(rating_stats[0] or 0.0), 1),
        rating_count=int(rating_stats[1] or 0),
        created_at=capsule.created_at,
        updated_at=capsule.updated_at,
    )


@app.delete("/v1/capsules/{capsule_id}", status_code=204)
async def delete_capsule(
    capsule_id: str,
    db: Session = Depends(get_db),
):
    """Delete a capsule from marketplace.
    
    Args:
        capsule_id: Capsule UUID
        db: Database session
    """
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    # Cascade delete will handle versions, ratings, downloads
    db.delete(capsule)
    db.commit()
    
    return None


@app.post("/v1/capsules/{capsule_id}/ratings", response_model=RatingResponse, status_code=201)
async def rate_capsule(
    capsule_id: str,
    request: CapsuleRatingRequest,
    db: Session = Depends(get_db),
):
    """Submit a rating for a capsule.
    
    Args:
        capsule_id: Capsule UUID
        request: Rating request
        db: Database session
        
    Returns:
        Created rating
    """
    # Verify capsule exists
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    # Check if user already rated this capsule
    existing = db.query(CapsuleRating).filter(
        CapsuleRating.capsule_id == capsule_id,
        CapsuleRating.user_id == request.user_id,
    ).first()
    
    if existing:
        # Update existing rating
        existing.rating = request.rating
        existing.review = request.review
        db.commit()
        db.refresh(existing)
        rating = existing
    else:
        # Create new rating
        rating = CapsuleRating(
            capsule_id=capsule_id,
            user_id=request.user_id,
            rating=request.rating,
            review=request.review,
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
    
    return RatingResponse(
        id=rating.id,
        user_id=rating.user_id,
        rating=rating.rating,
        review=rating.review,
        created_at=rating.created_at,
    )


@app.post("/v1/capsules/{capsule_id}/downloads", status_code=201)
async def record_download(
    capsule_id: str,
    user_id: str = Query(..., description="Downloading user ID"),
    db: Session = Depends(get_db),
):
    """Record a capsule download event.
    
    Args:
        capsule_id: Capsule UUID
        user_id: User ID downloading capsule
        db: Database session
        
    Returns:
        Download count
    """
    # Verify capsule exists
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    # Record download
    download = CapsuleDownload(
        capsule_id=capsule_id,
        user_id=user_id,
    )
    db.add(download)
    db.commit()
    
    # Get total download count
    count = db.query(func.count(CapsuleDownload.id)).filter(
        CapsuleDownload.capsule_id == capsule_id
    ).scalar() or 0
    
    return {"capsule_id": capsule_id, "downloads": count}


@app.get("/v1/search", response_model=List[CapsuleResponse])
async def search_capsules(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search capsules by name, description, or tags.
    
    Args:
        q: Search query string
        limit: Max results
        db: Database session
        
    Returns:
        Matching capsules
    """
    search_term = f"%{q}%"
    
    capsules = db.query(Capsule).filter(
        or_(
            Capsule.name.ilike(search_term),
            Capsule.description.ilike(search_term),
            Capsule.tags.contains([q]),  # Exact tag match
        )
    ).limit(limit).all()
    
    results = []
    for capsule in capsules:
        download_count = db.query(func.count(CapsuleDownload.id)).filter(
            CapsuleDownload.capsule_id == capsule.id
        ).scalar() or 0
        
        rating_stats = db.query(
            func.avg(CapsuleRating.rating),
            func.count(CapsuleRating.id)
        ).filter(
            CapsuleRating.capsule_id == capsule.id
        ).first()
        
        latest_version = db.query(CapsuleVersion).filter(
            CapsuleVersion.capsule_id == capsule.id
        ).order_by(CapsuleVersion.created_at.desc()).first()
        
        results.append(CapsuleResponse(
            id=capsule.id,
            name=capsule.name,
            description=capsule.description,
            author=capsule.author,
            category=capsule.category,
            tags=capsule.tags,
            version=latest_version.version if latest_version else "1.0.0",
            downloads=download_count,
            rating=round(float(rating_stats[0] or 0.0), 1),
            rating_count=int(rating_stats[1] or 0),
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
        ))
    
    return results
