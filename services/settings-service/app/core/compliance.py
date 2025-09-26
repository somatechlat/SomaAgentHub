"""Compliance linting helpers for capsule submissions."""

from __future__ import annotations

import re
from datetime import datetime
from typing import List

from ..api.schemas import ComplianceIssue, ComplianceReport, CapsuleSubmissionRequest

VERSION_PATTERN = re.compile(r"^v?(\d+\.\d+\.\d+)$")


def run_compliance_lint(request: CapsuleSubmissionRequest) -> ComplianceReport:
    """Run lightweight linting rules and return a report."""

    issues: List[ComplianceIssue] = []

    if len(request.summary.strip()) < 20:
        issues.append(
            ComplianceIssue(
                code="SUMMARY_TOO_SHORT",
                severity="warning",
                message="Summary should describe capsule intent in at least 20 characters.",
            )
        )

    if not VERSION_PATTERN.match(request.version):
        issues.append(
            ComplianceIssue(
                code="VERSION_FORMAT",
                severity="error",
                message="Version must follow semantic versioning (e.g., 1.2.0).",
            )
        )

    metadata = request.metadata or {}
    if metadata.get("requires_approval") and not metadata.get("reviewers"):
        issues.append(
            ComplianceIssue(
                code="MISSING_REVIEWERS",
                severity="error",
                message="Capsule requires explicit reviewers but none were supplied.",
            )
        )

    passed = not any(issue.severity == "error" for issue in issues)
    return ComplianceReport(passed=passed, issues=issues)


def attestation_is_fresh(issued_at: datetime, tolerance_hours: int = 48) -> bool:
    """Check attestation freshness window."""

    delta = datetime.utcnow() - issued_at
    return delta.total_seconds() <= tolerance_hours * 3600
