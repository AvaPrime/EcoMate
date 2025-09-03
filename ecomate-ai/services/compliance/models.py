from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime, date
import re

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING = "pending"
    UNKNOWN = "unknown"

class RuleSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class RuleOperator(str, Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">" 
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"

class StandardType(str, Enum):
    SANS = "sans"
    ISO = "iso"
    EPA = "epa"
    CE = "ce"
    NSF = "nsf"
    CUSTOM = "custom"

class SystemType(str, Enum):
    WATER_TREATMENT = "water_treatment"
    WASTEWATER_TREATMENT = "wastewater_treatment"
    UV_DISINFECTION = "uv_disinfection"
    MEMBRANE_FILTRATION = "membrane_filtration"
    CHEMICAL_DOSING = "chemical_dosing"
    PUMPING_SYSTEM = "pumping_system"
    STORAGE_TANK = "storage_tank"
    CONTROL_SYSTEM = "control_system"

class RuleCondition(BaseModel):
    """Individual rule condition with operator and threshold"""
    field: str = Field(..., description="Field name to evaluate")
    operator: RuleOperator = Field(..., description="Comparison operator")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Threshold or expected value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    description: Optional[str] = Field(None, description="Human-readable description")

class ComplianceRule(BaseModel):
    """Enhanced compliance rule with structured evaluation"""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Detailed rule description")
    standard_type: StandardType = Field(..., description="Standard/regulation type")
    standard_version: Optional[str] = Field(None, description="Version of the standard")
    section_reference: Optional[str] = Field(None, description="Section/clause reference")
    system_types: List[SystemType] = Field(..., description="Applicable system types")
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Rule severity level")
    conditions: List[RuleCondition] = Field(..., description="Rule conditions to evaluate")
    logic_operator: str = Field(default="AND", description="Logic operator for multiple conditions (AND/OR)")
    remediation_guidance: Optional[str] = Field(None, description="Guidance for remediation")
    references: List[str] = Field(default_factory=list, description="Reference documents/URLs")
    effective_date: Optional[date] = Field(None, description="Rule effective date")
    expiry_date: Optional[date] = Field(None, description="Rule expiry date")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    
    @field_validator('rule_id')
    @classmethod
    def validate_rule_id(cls, v):
        if not re.match(r'^[A-Z0-9_]+$', v):
            raise ValueError('Rule ID must contain only uppercase letters, numbers, and underscores')
        return v

class RuleSet(BaseModel):
    """Collection of related compliance rules"""
    ruleset_id: str = Field(..., description="Unique ruleset identifier")
    name: str = Field(..., description="Ruleset name")
    description: str = Field(..., description="Ruleset description")
    standard_type: StandardType = Field(..., description="Standard type")
    version: str = Field(..., description="Ruleset version")
    jurisdiction: Optional[str] = Field(None, description="Applicable jurisdiction")
    rules: List[ComplianceRule] = Field(..., description="Rules in this set")
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)
    author: Optional[str] = Field(None, description="Ruleset author")
    approval_status: str = Field(default="draft", description="Approval status")

class EvaluationResult(BaseModel):
    """Result of evaluating a single rule condition"""
    condition: RuleCondition
    actual_value: Any = Field(..., description="Actual value from specification")
    expected_value: Any = Field(..., description="Expected value from rule")
    passed: bool = Field(..., description="Whether condition passed")
    message: str = Field(..., description="Evaluation message")
    severity: RuleSeverity = Field(..., description="Severity level")

class RuleEvaluationResult(BaseModel):
    """Result of evaluating a complete rule"""
    rule: ComplianceRule
    status: ComplianceStatus = Field(..., description="Overall rule compliance status")
    condition_results: List[EvaluationResult] = Field(..., description="Individual condition results")
    passed_conditions: int = Field(..., description="Number of passed conditions")
    total_conditions: int = Field(..., description="Total number of conditions")
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    evaluation_timestamp: datetime = Field(default_factory=datetime.now)
    remediation_required: bool = Field(..., description="Whether remediation is required")
    remediation_priority: RuleSeverity = Field(..., description="Remediation priority")

class ComplianceReport(BaseModel):
    """Comprehensive compliance evaluation report"""
    report_id: str = Field(..., description="Unique report identifier")
    system_id: str = Field(..., description="System being evaluated")
    system_type: SystemType = Field(..., description="Type of system")
    evaluation_date: datetime = Field(default_factory=datetime.now)
    rulesets_evaluated: List[str] = Field(..., description="Rulesets used in evaluation")
    overall_status: ComplianceStatus = Field(..., description="Overall compliance status")
    overall_score: float = Field(..., description="Overall compliance score (0-100)")
    rule_results: List[RuleEvaluationResult] = Field(..., description="Individual rule results")
    
    # Summary statistics
    total_rules: int = Field(..., description="Total rules evaluated")
    passed_rules: int = Field(..., description="Number of passed rules")
    failed_rules: int = Field(..., description="Number of failed rules")
    critical_failures: int = Field(..., description="Number of critical failures")
    high_priority_failures: int = Field(..., description="Number of high priority failures")
    
    # Remediation information
    remediation_required: bool = Field(..., description="Whether remediation is required")
    remediation_items: List[Dict[str, Any]] = Field(default_factory=list, description="Remediation action items")
    estimated_remediation_cost: Optional[float] = Field(None, description="Estimated remediation cost")
    estimated_remediation_time: Optional[str] = Field(None, description="Estimated remediation time")
    
    # Metadata
    evaluator: Optional[str] = Field(None, description="Who performed the evaluation")
    specification_data: Dict[str, Any] = Field(..., description="System specification data used")
    notes: Optional[str] = Field(None, description="Additional notes")
    attachments: List[str] = Field(default_factory=list, description="Attachment file paths")

class ComplianceFilter(BaseModel):
    """Filter criteria for compliance queries"""
    standard_types: Optional[List[StandardType]] = None
    system_types: Optional[List[SystemType]] = None
    severity_levels: Optional[List[RuleSeverity]] = None
    compliance_status: Optional[List[ComplianceStatus]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    jurisdiction: Optional[str] = None

class SystemSpecification(BaseModel):
    """System specification for compliance evaluation"""
    system_id: str = Field(..., description="Unique system identifier")
    system_type: SystemType = Field(..., description="Type of system")
    name: str = Field(..., description="System name")
    description: Optional[str] = Field(None, description="System description")
    specifications: Dict[str, Any] = Field(..., description="Technical specifications")
    design_parameters: Dict[str, Any] = Field(default_factory=dict, description="Design parameters")
    operational_parameters: Dict[str, Any] = Field(default_factory=dict, description="Operational parameters")
    performance_data: Dict[str, Any] = Field(default_factory=dict, description="Performance data")
    installation_details: Dict[str, Any] = Field(default_factory=dict, description="Installation details")
    jurisdiction: Optional[str] = Field(None, description="Installation jurisdiction")
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)

class RegulatoryUpdate(BaseModel):
    """Regulatory update notification"""
    update_id: str = Field(..., description="Unique update identifier")
    standard_type: StandardType = Field(..., description="Standard type")
    title: str = Field(..., description="Update title")
    description: str = Field(..., description="Update description")
    change_type: str = Field(..., description="Type of change (new, modified, withdrawn)")
    effective_date: date = Field(..., description="Effective date")
    impact_assessment: Optional[str] = Field(None, description="Impact assessment")
    affected_rules: List[str] = Field(default_factory=list, description="Affected rule IDs")
    source_url: Optional[str] = Field(None, description="Source URL")
    notification_date: datetime = Field(default_factory=datetime.now)
    processed: bool = Field(default=False, description="Whether update has been processed")

class ComplianceMetrics(BaseModel):
    """Compliance metrics and KPIs"""
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    total_evaluations: int = Field(..., description="Total evaluations performed")
    compliance_rate: float = Field(..., description="Overall compliance rate")
    average_score: float = Field(..., description="Average compliance score")
    critical_failures_rate: float = Field(..., description="Critical failures rate")
    remediation_completion_rate: float = Field(..., description="Remediation completion rate")
    most_common_failures: List[Dict[str, Any]] = Field(default_factory=list, description="Most common failure types")
    trend_data: Dict[str, List[float]] = Field(default_factory=dict, description="Trend data over time")
    system_type_breakdown: Dict[SystemType, Dict[str, float]] = Field(default_factory=dict, description="Metrics by system type")