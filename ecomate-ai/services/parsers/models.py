from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class SupplierRow(BaseModel):
    sku: str = Field(..., description="Supplier stock keeping unit")
    name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    currency: Optional[str] = None
    price: Optional[float] = None
    availability: Optional[str] = None
    moq: Optional[str] = None
    lead_time: Optional[str] = None
    notes: Optional[str] = None
    last_seen: Optional[str] = None

    @field_validator('currency')
    @classmethod
    def cur_upper(cls, v):
        return v.upper() if isinstance(v, str) else v

class PartRow(BaseModel):
    part_number: str = Field(...)
    description: Optional[str] = None
    category: Optional[str] = None
    specs_json: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    supplier: Optional[str] = None
    sku: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    last_seen: Optional[str] = None

# Domain objects for richer validation
class Pump(BaseModel):
    model: str
    brand: Optional[str] = None
    flow_m3h: Optional[float] = Field(None, description="Nominal flow in m^3/h")
    head_m: Optional[float] = Field(None, description="Nominal head in meters")
    power_kw: Optional[float] = None
    voltage_v: Optional[int] = None
    phase: Optional[Literal['1','3']] = None
    material: Optional[str] = None

class UVReactor(BaseModel):
    model: str
    brand: Optional[str] = None
    flow_m3h: Optional[float] = None
    dose_mj_cm2: Optional[float] = None
    lamp_w: Optional[int] = None
    lamps_qty: Optional[int] = None
    chamber_material: Optional[str] = None