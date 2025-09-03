"""Pydantic models for regulatory monitoring and compliance tracking."""

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from decimal import Decimal


class StandardsBody(str, Enum):
    """Enumeration of supported standards bodies."""
    SANS = "SANS"  # South African National Standards
    ISO = "ISO"    # International Organization for Standardization
    EPA = "EPA"    # Environmental Protection Agency
    OSHA = "OSHA"  # Occupational Safety and Health Administration
    ANSI = "ANSI"  # American National Standards Institute
    ASTM = "ASTM"  # American Society for Testing and Materials
    IEC = "IEC"    # International Electrotechnical Commission
    IEEE = "IEEE"  # Institute of Electrical and Electronics Engineers


class ComplianceStatus(str, Enum):
    """Compliance status enumeration."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    EXPIRED = "expired"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StandardCategory(str, Enum):
    """Categories of regulatory standards."""
    ENVIRONMENTAL = "environmental"
    SAFETY = "safety"
    QUALITY = "quality"
    SECURITY = "security"
    TECHNICAL = "technical"
    MANAGEMENT = "management"
    PROCESS = "process"
    PRODUCT = "product"


class UpdateType(str, Enum):
    """Types of standards updates."""
    NEW_STANDARD = "new_standard"
    REVISION = "revision"
    AMENDMENT = "amendment"
    WITHDRAWAL = "withdrawal"
    CONFIRMATION = "confirmation"
    CORRECTION = "correction"


class RegulatoryStandard(BaseModel):
    """Model for regulatory standards information."""
    id: str = Field(..., description="Unique standard identifier")
    title: str = Field(..., description="Standard title")
    body: StandardsBody = Field(..., description="Standards body")
    category: StandardCategory = Field(..., description="Standard category")
    number: str = Field(..., description="Standard number/code")
    version: str = Field(..., description="Standard version")
    publication_date: date = Field(..., description="Publication date")
    effective_date: Optional[date] = Field(None, description="Effective date")
    review_date: Optional[date] = Field(None, description="Next review date")
    status: str = Field(..., description="Standard status")
    abstract: Optional[str] = Field(None, description="Standard abstract")
    scope: Optional[str] = Field(None, description="Standard scope")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    related_standards: List[str] = Field(default_factory=list, description="Related standards")
    supersedes: Optional[str] = Field(None, description="Superseded standard")
    superseded_by: Optional[str] = Field(None, description="Superseding standard")
    price: Optional[Decimal] = Field(None, description="Standard price")
    currency: Optional[str] = Field(None, description="Price currency")
    pages: Optional[int] = Field(None, description="Number of pages")
    language: str = Field(default="en", description="Standard language")
    url: Optional[str] = Field(None, description="Standard URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v

    @validator('pages')
    def validate_pages(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Pages must be positive')
        return v


class ComplianceRequirement(BaseModel):
    """Model for compliance requirements."""
    id: str = Field(..., description="Requirement identifier")
    standard_id: str = Field(..., description="Associated standard ID")
    title: str = Field(..., description="Requirement title")
    description: str = Field(..., description="Requirement description")
    section: Optional[str] = Field(None, description="Standard section")
    mandatory: bool = Field(True, description="Whether requirement is mandatory")
    applicable_to: List[str] = Field(default_factory=list, description="Applicable entities")
    verification_method: Optional[str] = Field(None, description="Verification method")
    evidence_required: List[str] = Field(default_factory=list, description="Required evidence")
    frequency: Optional[str] = Field(None, description="Compliance check frequency")
    deadline: Optional[date] = Field(None, description="Compliance deadline")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level (1-5)")


class ComplianceCheck(BaseModel):
    """Model for compliance check results."""
    id: str = Field(..., description="Check identifier")
    requirement_id: str = Field(..., description="Associated requirement ID")
    entity_id: str = Field(..., description="Entity being checked")
    status: ComplianceStatus = Field(..., description="Compliance status")
    check_date: datetime = Field(..., description="Check date and time")
    assessor: Optional[str] = Field(None, description="Assessor name")
    score: Optional[float] = Field(None, ge=0, le=1, description="Compliance score (0-1)")
    findings: List[str] = Field(default_factory=list, description="Check findings")
    evidence: List[str] = Field(default_factory=list, description="Evidence references")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    next_check_date: Optional[date] = Field(None, description="Next check date")
    remediation_required: bool = Field(default=False, description="Remediation needed")
    remediation_deadline: Optional[date] = Field(None, description="Remediation deadline")
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('score')
    def validate_score(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError('Score must be between 0 and 1')
        return v


class RegulatoryAlert(BaseModel):
    """Model for regulatory alerts and notifications."""
    id: str = Field(..., description="Alert identifier")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    severity: AlertSeverity = Field(..., description="Alert severity")
    body: StandardsBody = Field(..., description="Standards body")
    standard_id: Optional[str] = Field(None, description="Related standard ID")
    alert_type: str = Field(..., description="Type of alert")
    created_at: datetime = Field(..., description="Alert creation time")
    effective_date: Optional[date] = Field(None, description="Alert effective date")
    expiry_date: Optional[date] = Field(None, description="Alert expiry date")
    affected_entities: List[str] = Field(default_factory=list, description="Affected entities")
    action_required: bool = Field(default=False, description="Action required")
    action_deadline: Optional[date] = Field(None, description="Action deadline")
    url: Optional[str] = Field(None, description="Alert URL")
    acknowledged: bool = Field(default=False, description="Alert acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Acknowledged by")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StandardsUpdate(BaseModel):
    """Model for standards updates and changes."""
    id: str = Field(..., description="Update identifier")
    standard_id: str = Field(..., description="Updated standard ID")
    update_type: UpdateType = Field(..., description="Type of update")
    title: str = Field(..., description="Update title")
    description: str = Field(..., description="Update description")
    publication_date: date = Field(..., description="Update publication date")
    effective_date: Optional[date] = Field(None, description="Update effective date")
    changes: List[str] = Field(default_factory=list, description="List of changes")
    impact_assessment: Optional[str] = Field(None, description="Impact assessment")
    transition_period: Optional[int] = Field(None, description="Transition period in days")
    previous_version: Optional[str] = Field(None, description="Previous version")
    new_version: str = Field(..., description="New version")
    url: Optional[str] = Field(None, description="Update URL")
    documents: List[str] = Field(default_factory=list, description="Related documents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ComplianceReport(BaseModel):
    """Model for compliance reports."""
    id: str = Field(..., description="Report identifier")
    title: str = Field(..., description="Report title")
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    report_date: date = Field(..., description="Report date")
    period_start: date = Field(..., description="Reporting period start")
    period_end: date = Field(..., description="Reporting period end")
    overall_status: ComplianceStatus = Field(..., description="Overall compliance status")
    overall_score: Optional[float] = Field(None, ge=0, le=1, description="Overall score")
    standards_assessed: List[str] = Field(..., description="Standards assessed")
    checks_performed: int = Field(..., ge=0, description="Number of checks performed")
    compliant_checks: int = Field(..., ge=0, description="Number of compliant checks")
    non_compliant_checks: int = Field(..., ge=0, description="Number of non-compliant checks")
    findings: List[str] = Field(default_factory=list, description="Key findings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    action_items: List[str] = Field(default_factory=list, description="Action items")
    next_assessment_date: Optional[date] = Field(None, description="Next assessment date")
    assessor: Optional[str] = Field(None, description="Assessor name")
    approved_by: Optional[str] = Field(None, description="Approved by")
    approval_date: Optional[date] = Field(None, description="Approval date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('compliant_checks', 'non_compliant_checks')
    def validate_check_counts(cls, v, values):
        if 'checks_performed' in values and v > values['checks_performed']:
            raise ValueError('Check counts cannot exceed total checks performed')
        return v


class RegulatoryQuery(BaseModel):
    """Model for regulatory queries."""
    query_type: str = Field(..., description="Type of query")
    body: Optional[StandardsBody] = Field(None, description="Standards body")
    standard_id: Optional[str] = Field(None, description="Standard ID")
    category: Optional[StandardCategory] = Field(None, description="Standard category")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")
    date_from: Optional[date] = Field(None, description="Date range start")
    date_to: Optional[date] = Field(None, description="Date range end")
    status_filter: Optional[ComplianceStatus] = Field(None, description="Status filter")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    include_metadata: bool = Field(default=False, description="Include metadata")
    limit: int = Field(default=100, ge=1, le=1000, description="Result limit")
    offset: int = Field(default=0, ge=0, description="Result offset")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order")


class RegulatoryResponse(BaseModel):
    """Model for regulatory service responses."""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(None, description="Response data")
    total_count: Optional[int] = Field(None, description="Total result count")
    page_count: Optional[int] = Field(None, description="Page count")
    current_page: Optional[int] = Field(None, description="Current page")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    errors: List[str] = Field(default_factory=list, description="Errors")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BatchRegulatoryRequest(BaseModel):
    """Model for batch regulatory requests."""
    requests: List[RegulatoryQuery] = Field(..., min_items=1, max_items=100, description="Batch requests")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    priority: int = Field(default=1, ge=1, le=5, description="Batch priority")
    callback_url: Optional[str] = Field(None, description="Callback URL for results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Batch metadata")


class BatchRegulatoryResponse(BaseModel):
    """Model for batch regulatory responses."""
    batch_id: str = Field(..., description="Batch identifier")
    total_requests: int = Field(..., description="Total requests in batch")
    completed_requests: int = Field(..., description="Completed requests")
    failed_requests: int = Field(..., description="Failed requests")
    responses: List[RegulatoryResponse] = Field(..., description="Individual responses")
    batch_status: str = Field(..., description="Batch processing status")
    started_at: datetime = Field(..., description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")
    total_processing_time: Optional[float] = Field(None, description="Total processing time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Batch metadata")


class RegulatoryConfig(BaseModel):
    """Model for regulatory service configuration."""
    update_interval: int = Field(default=3600, ge=60, description="Update interval in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retries")
    timeout: int = Field(default=30, ge=5, le=300, description="Request timeout in seconds")
    cache_ttl: int = Field(default=1800, ge=60, description="Cache TTL in seconds")
    batch_size: int = Field(default=50, ge=1, le=100, description="Batch processing size")
    alert_threshold: float = Field(default=0.8, ge=0, le=1, description="Alert threshold")
    enable_notifications: bool = Field(default=True, description="Enable notifications")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")
    log_level: str = Field(default="INFO", description="Logging level")
    api_keys: Dict[str, str] = Field(default_factory=dict, description="API keys")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")