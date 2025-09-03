from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class ComponentType(str, Enum):
    PUMP = "pump"
    BLOWER = "blower"
    TANK = "tank"
    PIPE = "pipe"
    VALVE = "valve"
    SENSOR = "sensor"
    CONTROL = "control"
    ELECTRICAL = "electrical"
    CHEMICAL = "chemical"
    MEMBRANE = "membrane"
    FILTER = "filter"
    OTHER = "other"

class Component(BaseModel):
    id: str = Field(..., description="Unique component identifier")
    name: str = Field(..., description="Component name")
    type: ComponentType = Field(..., description="Component type")
    manufacturer: str = Field(..., description="Manufacturer name")
    model: str = Field(..., description="Model number")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Technical specifications")
    unit_cost: float = Field(..., description="Cost per unit in USD")
    installation_cost: float = Field(default=0.0, description="Installation cost in USD")
    maintenance_cost_annual: float = Field(default=0.0, description="Annual maintenance cost in USD")
    lifespan_years: int = Field(default=10, description="Expected lifespan in years")
    energy_consumption_kwh: float = Field(default=0.0, description="Energy consumption in kWh")
    efficiency_rating: Optional[float] = Field(None, description="Efficiency rating (0-1)")
    environmental_impact_score: Optional[float] = Field(None, description="Environmental impact score")

class BOMItem(BaseModel):
    component: Component = Field(..., description="Component details")
    quantity: int = Field(..., description="Required quantity")
    total_cost: float = Field(..., description="Total cost for this item")
    installation_time_hours: float = Field(default=0.0, description="Installation time in hours")
    notes: Optional[str] = Field(None, description="Additional notes")

class BillOfMaterials(BaseModel):
    id: str = Field(..., description="BOM unique identifier")
    project_id: str = Field(..., description="Associated project ID")
    items: List[BOMItem] = Field(..., description="List of BOM items")
    total_material_cost: float = Field(..., description="Total material cost")
    total_installation_cost: float = Field(..., description="Total installation cost")
    total_cost: float = Field(..., description="Total BOM cost")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0", description="BOM version")

class ProjectRequirements(BaseModel):
    flow_rate_mgd: float = Field(..., description="Flow rate in million gallons per day")
    treatment_type: str = Field(..., description="Type of treatment required")
    effluent_standards: Dict[str, float] = Field(..., description="Required effluent standards")
    site_constraints: Dict[str, Any] = Field(default_factory=dict, description="Site-specific constraints")
    budget_range: Optional[Dict[str, float]] = Field(None, description="Budget range (min/max)")
    timeline_months: Optional[int] = Field(None, description="Project timeline in months")
    special_requirements: List[str] = Field(default_factory=list, description="Special requirements")

class CostBreakdown(BaseModel):
    materials: float = Field(..., description="Material costs")
    labor: float = Field(..., description="Labor costs")
    equipment: float = Field(..., description="Equipment costs")
    engineering: float = Field(..., description="Engineering costs")
    permits: float = Field(..., description="Permit costs")
    contingency: float = Field(..., description="Contingency costs")
    total: float = Field(..., description="Total project cost")

class ROICalculation(BaseModel):
    initial_investment: float = Field(..., description="Initial investment cost")
    annual_operating_cost: float = Field(..., description="Annual operating cost")
    annual_savings: float = Field(..., description="Annual cost savings")
    payback_period_years: float = Field(..., description="Payback period in years")
    net_present_value: float = Field(..., description="Net present value")
    internal_rate_return: float = Field(..., description="Internal rate of return")
    discount_rate: float = Field(default=0.08, description="Discount rate used")
    analysis_period_years: int = Field(default=20, description="Analysis period in years")

class Proposal(BaseModel):
    id: str = Field(..., description="Proposal unique identifier")
    project_name: str = Field(..., description="Project name")
    client_name: str = Field(..., description="Client name")
    requirements: ProjectRequirements = Field(..., description="Project requirements")
    bom: BillOfMaterials = Field(..., description="Bill of materials")
    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown")
    roi_calculation: ROICalculation = Field(..., description="ROI calculation")
    timeline_months: int = Field(..., description="Project timeline")
    warranty_years: int = Field(default=2, description="Warranty period")
    proposal_valid_until: datetime = Field(..., description="Proposal validity date")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="draft", description="Proposal status")
    notes: Optional[str] = Field(None, description="Additional notes")
    attachments: List[str] = Field(default_factory=list, description="Attachment file paths")

class Quote(BaseModel):
    """Quote model for cost calculations"""
    bom: List[Dict[str, Any]] = Field(..., description="Bill of materials items")
    materials_subtotal: float = Field(..., description="Materials subtotal")
    labour: float = Field(..., description="Labour costs")
    logistics: float = Field(..., description="Logistics costs")
    opex_year1: float = Field(..., description="First year operational expenses")
    total_before_margin: float = Field(..., description="Total before margin")
    total_quote: float = Field(..., description="Final quoted total")

class ClientContext(BaseModel):
    """Client context information"""
    name: str = Field(..., description="Client name")
    location: Optional[str] = Field(None, description="Client location")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")

class SystemSpec(BaseModel):
    """System specification model"""
    type: str = Field(..., description="System type")
    capacity_lpd: Optional[float] = Field(None, description="Capacity in liters per day")
    offgrid: bool = Field(default=False, description="Off-grid system flag")
    flow_rate_mgd: Optional[float] = Field(None, description="Flow rate in MGD")
    treatment_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Treatment requirements")

class Assumptions(BaseModel):
    """Project assumptions model"""
    distance_km: float = Field(default=50.0, description="Distance in kilometers")
    installation_complexity: str = Field(default="standard", description="Installation complexity")
    site_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Site conditions")
    timeline_constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Timeline constraints")