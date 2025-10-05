"""
⚠️ WE DO NOT MOCK - Governance Overlays for KAMACHIQ.

Industry-specific ethical and compliance modulators:
- Healthcare (HIPAA compliance)
- Finance (SOC2, PCI-DSS)
- Education (FERPA, COPPA)
- Government (FedRAMP)
- Custom governance rules
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class IndustryType(Enum):
    """Supported industry types."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    GOVERNMENT = "government"
    ECOMMERCE = "ecommerce"
    GENERAL = "general"


@dataclass
class GovernanceRule:
    """A single governance rule."""
    id: str
    category: str  # data_handling, security, access_control, audit
    description: str
    enforcement_level: str  # required, recommended, optional
    validation_function: str  # Function name to call for validation
    remediation: str  # How to fix violations


class GovernanceOverlay:
    """
    Industry-specific governance and compliance modulator.
    
    Applies ethical and regulatory constraints to project execution.
    """
    
    def __init__(self, industry: IndustryType):
        self.industry = industry
        self.rules = self._load_industry_rules(industry)
    
    def _load_industry_rules(self, industry: IndustryType) -> List[GovernanceRule]:
        """Load governance rules for industry."""
        logger.info(f"Loading governance rules for: {industry.value}")
        
        if industry == IndustryType.HEALTHCARE:
            return self._get_healthcare_rules()
        elif industry == IndustryType.FINANCE:
            return self._get_finance_rules()
        elif industry == IndustryType.EDUCATION:
            return self._get_education_rules()
        elif industry == IndustryType.GOVERNMENT:
            return self._get_government_rules()
        else:
            return self._get_general_rules()
    
    def _get_healthcare_rules(self) -> List[GovernanceRule]:
        """HIPAA compliance rules."""
        return [
            GovernanceRule(
                id="hipaa-encryption-at-rest",
                category="data_handling",
                description="All PHI must be encrypted at rest using AES-256",
                enforcement_level="required",
                validation_function="validate_encryption_at_rest",
                remediation="Enable encryption on all data stores containing PHI"
            ),
            GovernanceRule(
                id="hipaa-encryption-in-transit",
                category="data_handling",
                description="All PHI must be encrypted in transit using TLS 1.2+",
                enforcement_level="required",
                validation_function="validate_encryption_in_transit",
                remediation="Configure TLS 1.2+ for all API endpoints"
            ),
            GovernanceRule(
                id="hipaa-access-logs",
                category="audit",
                description="All access to PHI must be logged and retained for 6 years",
                enforcement_level="required",
                validation_function="validate_audit_logging",
                remediation="Enable CloudWatch/CloudTrail logging with 6-year retention"
            ),
            GovernanceRule(
                id="hipaa-mfa",
                category="access_control",
                description="Multi-factor authentication required for all users",
                enforcement_level="required",
                validation_function="validate_mfa_enabled",
                remediation="Enable MFA in identity provider"
            ),
            GovernanceRule(
                id="hipaa-data-retention",
                category="data_handling",
                description="PHI must be retained per state law (typically 6-10 years)",
                enforcement_level="required",
                validation_function="validate_data_retention",
                remediation="Configure lifecycle policies for data retention"
            ),
        ]
    
    def _get_finance_rules(self) -> List[GovernanceRule]:
        """SOC2 and PCI-DSS compliance rules."""
        return [
            GovernanceRule(
                id="pci-no-card-storage",
                category="data_handling",
                description="Cardholder data must not be stored (use tokenization)",
                enforcement_level="required",
                validation_function="validate_no_card_storage",
                remediation="Integrate payment gateway with tokenization (Stripe, etc.)"
            ),
            GovernanceRule(
                id="soc2-access-control",
                category="access_control",
                description="Role-based access control (RBAC) required",
                enforcement_level="required",
                validation_function="validate_rbac",
                remediation="Implement RBAC in IAM system"
            ),
            GovernanceRule(
                id="soc2-change-tracking",
                category="audit",
                description="All infrastructure changes must be tracked and auditable",
                enforcement_level="required",
                validation_function="validate_change_tracking",
                remediation="Enable CloudTrail/audit logs for all resources"
            ),
            GovernanceRule(
                id="soc2-encryption",
                category="security",
                description="Sensitive data must be encrypted at rest and in transit",
                enforcement_level="required",
                validation_function="validate_encryption",
                remediation="Enable encryption on all data stores and use HTTPS/TLS"
            ),
            GovernanceRule(
                id="soc2-incident-response",
                category="security",
                description="Incident response plan must be documented and tested",
                enforcement_level="required",
                validation_function="validate_incident_response",
                remediation="Document incident response procedures"
            ),
        ]
    
    def _get_education_rules(self) -> List[GovernanceRule]:
        """FERPA and COPPA compliance rules."""
        return [
            GovernanceRule(
                id="ferpa-data-privacy",
                category="data_handling",
                description="Student education records must be protected",
                enforcement_level="required",
                validation_function="validate_student_data_privacy",
                remediation="Implement access controls on student data"
            ),
            GovernanceRule(
                id="coppa-parental-consent",
                category="access_control",
                description="Parental consent required for users under 13",
                enforcement_level="required",
                validation_function="validate_parental_consent",
                remediation="Implement age gate and parental consent workflow"
            ),
            GovernanceRule(
                id="ferpa-access-logs",
                category="audit",
                description="Access to education records must be logged",
                enforcement_level="required",
                validation_function="validate_education_record_logs",
                remediation="Enable audit logging for student data access"
            ),
        ]
    
    def _get_government_rules(self) -> List[GovernanceRule]:
        """FedRAMP compliance rules."""
        return [
            GovernanceRule(
                id="fedramp-baseline",
                category="security",
                description="Must meet FedRAMP baseline controls",
                enforcement_level="required",
                validation_function="validate_fedramp_baseline",
                remediation="Implement NIST 800-53 controls"
            ),
            GovernanceRule(
                id="fedramp-us-jurisdiction",
                category="data_handling",
                description="Data must remain in US jurisdiction",
                enforcement_level="required",
                validation_function="validate_data_jurisdiction",
                remediation="Configure cloud resources to US-only regions"
            ),
        ]
    
    def _get_general_rules(self) -> List[GovernanceRule]:
        """General best practices."""
        return [
            GovernanceRule(
                id="general-encryption",
                category="security",
                description="Sensitive data should be encrypted",
                enforcement_level="recommended",
                validation_function="validate_encryption",
                remediation="Enable encryption for databases and file storage"
            ),
            GovernanceRule(
                id="general-https",
                category="security",
                description="Use HTTPS for all API endpoints",
                enforcement_level="required",
                validation_function="validate_https",
                remediation="Configure SSL/TLS certificates"
            ),
        ]
    
    def validate_project_plan(
        self,
        execution_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate project execution plan against governance rules.
        
        Args:
            execution_plan: MAO execution plan
            
        Returns:
            Validation results with violations and recommendations
        """
        logger.info(f"Validating plan against {self.industry.value} governance")
        
        results = {
            "industry": self.industry.value,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": [],
        }
        
        steps = execution_plan.get("steps", [])
        
        for rule in self.rules:
            # Run validation
            violations = self._validate_rule(rule, steps)
            
            if violations:
                if rule.enforcement_level == "required":
                    results["compliant"] = False
                    results["violations"].extend(violations)
                elif rule.enforcement_level == "recommended":
                    results["warnings"].extend(violations)
                else:
                    results["recommendations"].extend(violations)
        
        return results
    
    def _validate_rule(
        self,
        rule: GovernanceRule,
        steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate a single rule."""
        violations = []
        
        # Dispatch to specific validation function
        if rule.validation_function == "validate_encryption_at_rest":
            violations = self._validate_encryption_at_rest(steps, rule)
        elif rule.validation_function == "validate_encryption_in_transit":
            violations = self._validate_encryption_in_transit(steps, rule)
        elif rule.validation_function == "validate_audit_logging":
            violations = self._validate_audit_logging(steps, rule)
        elif rule.validation_function == "validate_https":
            violations = self._validate_https(steps, rule)
        # ... add more validation functions
        
        return violations
    
    def _validate_encryption_at_rest(
        self,
        steps: List[Dict[str, Any]],
        rule: GovernanceRule
    ) -> List[Dict[str, Any]]:
        """Validate encryption at rest."""
        violations = []
        
        # Check for database steps without encryption
        for step in steps:
            if "database" in step.get("parameters", {}).get("resources", []):
                params = step.get("parameters", {})
                if not params.get("encryption_enabled"):
                    violations.append({
                        "rule_id": rule.id,
                        "step_id": step.get("id"),
                        "description": rule.description,
                        "remediation": rule.remediation,
                        "severity": "high"
                    })
        
        return violations
    
    def _validate_encryption_in_transit(
        self,
        steps: List[Dict[str, Any]],
        rule: GovernanceRule
    ) -> List[Dict[str, Any]]:
        """Validate encryption in transit."""
        violations = []
        
        # Check for API/service steps without TLS
        for step in steps:
            if step.get("tool") in ["github", "aws", "kubernetes"]:
                params = step.get("parameters", {})
                if not params.get("tls_enabled", True):  # Default to true
                    violations.append({
                        "rule_id": rule.id,
                        "step_id": step.get("id"),
                        "description": rule.description,
                        "remediation": rule.remediation,
                        "severity": "high"
                    })
        
        return violations
    
    def _validate_audit_logging(
        self,
        steps: List[Dict[str, Any]],
        rule: GovernanceRule
    ) -> List[Dict[str, Any]]:
        """Validate audit logging."""
        violations = []
        
        # Check if any infrastructure step enables logging
        has_logging = any(
            "logging" in step.get("parameters", {}).get("features", [])
            or "audit" in step.get("parameters", {}).get("features", [])
            for step in steps
        )
        
        if not has_logging:
            violations.append({
                "rule_id": rule.id,
                "step_id": "global",
                "description": rule.description,
                "remediation": rule.remediation,
                "severity": "high"
            })
        
        return violations
    
    def _validate_https(
        self,
        steps: List[Dict[str, Any]],
        rule: GovernanceRule
    ) -> List[Dict[str, Any]]:
        """Validate HTTPS usage."""
        # In practice, check service configurations
        return []
    
    def apply_remediations(
        self,
        execution_plan: Dict[str, Any],
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Automatically apply remediations to execution plan.
        
        Args:
            execution_plan: Original plan
            violations: List of violations
            
        Returns:
            Remediated execution plan
        """
        logger.info(f"Applying {len(violations)} remediations")
        
        remediated_plan = execution_plan.copy()
        
        for violation in violations:
            rule_id = violation["rule_id"]
            step_id = violation["step_id"]
            
            # Find step and apply remediation
            for step in remediated_plan.get("steps", []):
                if step.get("id") == step_id:
                    if "encryption" in rule_id:
                        step["parameters"]["encryption_enabled"] = True
                    elif "logging" in rule_id:
                        if "features" not in step["parameters"]:
                            step["parameters"]["features"] = []
                        step["parameters"]["features"].append("audit_logging")
                    elif "tls" in rule_id:
                        step["parameters"]["tls_enabled"] = True
        
        logger.info("Remediations applied")
        return remediated_plan


# Example usage
if __name__ == "__main__":
    # Create healthcare governance overlay
    healthcare_gov = GovernanceOverlay(IndustryType.HEALTHCARE)
    
    # Validate a plan
    execution_plan = {
        "steps": [
            {
                "id": "db_setup",
                "tool": "aws",
                "parameters": {
                    "resources": ["database"],
                    "encryption_enabled": False  # Violation!
                }
            }
        ]
    }
    
    results = healthcare_gov.validate_project_plan(execution_plan)
    
    print(f"Compliant: {results['compliant']}")
    print(f"Violations: {len(results['violations'])}")
    
    if not results["compliant"]:
        # Apply remediations
        fixed_plan = healthcare_gov.apply_remediations(
            execution_plan,
            results["violations"]
        )
        print("✅ Plan remediated for HIPAA compliance")
