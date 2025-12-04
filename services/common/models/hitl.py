"""
HITL Models - HumanReviewerAssignment, HumanDecisionRecord

SRS Section 10 - Human-in-the-Loop (HITL)
Tracks reviewer assignments and decisions for human review sessions.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base


# Enums
class ReviewerAssignmentStatus(str, Enum):
    """Status of a reviewer assignment"""
    ASSIGNED = "ASSIGNED"
    VIEWED = "VIEWED"
    ACTED = "ACTED"
    REASSIGNED = "REASSIGNED"
    EXPIRED = "EXPIRED"


class ReviewDecision(str, Enum):
    """Decision made by a human reviewer"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    ESCALATE = "ESCALATE"


# Models
class HumanReviewerAssignment(Base):
    """
    Assignment of a human reviewer to a review session.
    
    SRS Section 10.1 - HumanReviewerAssignment
    Tracks who is responsible for reviewing a session.
    """
    __tablename__ = "human_reviewer_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    review_session_id = Column(UUID(as_uuid=True), ForeignKey("human_review_sessions.id"), nullable=False, index=True)
    reviewer_principal_id = Column(UUID(as_uuid=True), ForeignKey("principals.id"), nullable=False, index=True)
    
    status = Column(SQLEnum(ReviewerAssignmentStatus), nullable=False, default=ReviewerAssignmentStatus.ASSIGNED)
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class HumanDecisionRecord(Base):
    """
    Record of a decision made by a human reviewer.
    
    SRS Section 10.2 - HumanDecisionRecord
    Audit trail of human interventions.
    """
    __tablename__ = "human_decision_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    review_session_id = Column(UUID(as_uuid=True), ForeignKey("human_review_sessions.id"), nullable=False, index=True)
    reviewer_principal_id = Column(UUID(as_uuid=True), ForeignKey("principals.id"), nullable=False)
    
    decision = Column(SQLEnum(ReviewDecision), nullable=False)
    comment = Column(Text, nullable=True)
    
    # Modifications
    diff_ref = Column(Text, nullable=True)  # Reference to diff if modified
    modified_payload_ref = Column(Text, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


# Pydantic models
from pydantic import BaseModel, Field
from uuid import UUID as PyUUID


class HumanReviewerAssignmentCreate(BaseModel):
    """API model for creating a reviewer assignment"""
    tenant_id: PyUUID
    review_session_id: PyUUID
    reviewer_principal_id: PyUUID


class HumanReviewerAssignmentResponse(BaseModel):
    """API model for reviewer assignment response"""
    id: PyUUID
    tenant_id: PyUUID
    review_session_id: PyUUID
    reviewer_principal_id: PyUUID
    status: ReviewerAssignmentStatus
    assigned_at: datetime
    viewed_at: Optional[datetime]
    acted_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HumanDecisionRecordCreate(BaseModel):
    """API model for creating a decision record"""
    tenant_id: PyUUID
    review_session_id: PyUUID
    reviewer_principal_id: PyUUID
    decision: ReviewDecision
    comment: Optional[str] = None
    diff_ref: Optional[str] = None
    modified_payload_ref: Optional[str] = None


class HumanDecisionRecordResponse(BaseModel):
    """API model for decision record response"""
    id: PyUUID
    tenant_id: PyUUID
    review_session_id: PyUUID
    reviewer_principal_id: PyUUID
    decision: ReviewDecision
    comment: Optional[str]
    diff_ref: Optional[str]
    modified_payload_ref: Optional[str]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
