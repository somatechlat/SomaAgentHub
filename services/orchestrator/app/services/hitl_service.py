"""
HITL Service - Manages human-in-the-loop review workflows.

SRS Section 10 - Human-in-the-Loop (HITL)
Handles reviewer assignments, notifications, and decision recording.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from services.common.models.hitl import (
    HumanReviewerAssignment, HumanDecisionRecord,
    ReviewerAssignmentStatus, ReviewDecision,
    HumanReviewerAssignmentCreate, HumanDecisionRecordCreate
)
from services.orchestrator.app.models.schema import HumanReviewSessionModel


class HITLService:
    """Service for managing HITL workflows"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Assignments ==========

    def assign_reviewer(self, assignment_create: HumanReviewerAssignmentCreate) -> HumanReviewerAssignment:
        """Assign a reviewer to a session"""
        # Validate session exists
        session = self.db.execute(
            select(HumanReviewSessionModel).where(
                HumanReviewSessionModel.id == assignment_create.review_session_id,
                HumanReviewSessionModel.tenant_id == assignment_create.tenant_id
            )
        ).scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review session {assignment_create.review_session_id} not found"
            )
            
        assignment = HumanReviewerAssignment(
            tenant_id=assignment_create.tenant_id,
            review_session_id=assignment_create.review_session_id,
            reviewer_principal_id=assignment_create.reviewer_principal_id,
            status=ReviewerAssignmentStatus.ASSIGNED
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        # TODO: Trigger notification (email/webhook)
        
        return assignment

    def get_assignment(self, assignment_id: UUID, tenant_id: UUID) -> Optional[HumanReviewerAssignment]:
        """Get an assignment by ID"""
        return self.db.execute(
            select(HumanReviewerAssignment).where(
                HumanReviewerAssignment.id == assignment_id,
                HumanReviewerAssignment.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    def list_assignments_for_session(self, session_id: UUID, tenant_id: UUID) -> List[HumanReviewerAssignment]:
        """List all assignments for a session"""
        return self.db.execute(
            select(HumanReviewerAssignment).where(
                HumanReviewerAssignment.review_session_id == session_id,
                HumanReviewerAssignment.tenant_id == tenant_id
            )
        ).scalars().all()

    # ========== Decisions ==========

    def record_decision(self, decision_create: HumanDecisionRecordCreate) -> HumanDecisionRecord:
        """Record a reviewer's decision"""
        # Validate session exists
        session = self.db.execute(
            select(HumanReviewSessionModel).where(
                HumanReviewSessionModel.id == decision_create.review_session_id,
                HumanReviewSessionModel.tenant_id == decision_create.tenant_id
            )
        ).scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review session {decision_create.review_session_id} not found"
            )
            
        decision = HumanDecisionRecord(
            tenant_id=decision_create.tenant_id,
            review_session_id=decision_create.review_session_id,
            reviewer_principal_id=decision_create.reviewer_principal_id,
            decision=decision_create.decision,
            comment=decision_create.comment,
            diff_ref=decision_create.diff_ref,
            modified_payload_ref=decision_create.modified_payload_ref
        )
        
        self.db.add(decision)
        
        # Update session status based on decision logic (simplified)
        # In a real system, this might require consensus or specific rules
        # For now, any decision resolves the session
        # session.status = ... (would need to update HumanReviewSessionModel status enum/logic)
        
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def get_decisions_for_session(self, session_id: UUID, tenant_id: UUID) -> List[HumanDecisionRecord]:
        """List all decisions for a session"""
        return self.db.execute(
            select(HumanDecisionRecord).where(
                HumanDecisionRecord.review_session_id == session_id,
                HumanDecisionRecord.tenant_id == tenant_id
            ).order_by(HumanDecisionRecord.timestamp)
        ).scalars().all()
