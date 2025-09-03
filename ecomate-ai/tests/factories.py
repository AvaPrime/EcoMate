"""Test data factories for EcoMate AI testing.

This module provides factory functions to create test data objects
for various services and models in the EcoMate AI system.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

import factory
from factory import Faker, LazyAttribute, SubFactory


class BaseFactory(factory.Factory):
    """Base factory with common attributes."""
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class SupplierFactory(BaseFactory):
    """Factory for supplier test data."""
    
    class Meta:
        model = dict
    
    name = Faker('company')
    website = Faker('url')
    contact_email = Faker('email')
    phone = Faker('phone_number')
    address = Faker('address')
    country = Faker('country')
    reliability_score = factory.LazyAttribute(lambda obj: round(random.uniform(0.7, 1.0), 2))
    api_endpoint = factory.LazyAttribute(lambda obj: f"https://api.{obj.name.lower().replace(' ', '')}.com")
    last_updated = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class ProductFactory(BaseFactory):
    """Factory for product test data."""
    
    class Meta:
        model = dict
    
    name = Faker('catch_phrase')
    model_number = factory.LazyAttribute(lambda obj: f"MDL-{random.randint(1000, 9999)}")
    category = factory.Iterator(['pump', 'uv_reactor', 'filter', 'valve', 'sensor'])
    supplier_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    price_usd = factory.LazyAttribute(lambda obj: round(random.uniform(100, 10000), 2))
    currency = 'USD'
    availability = factory.Iterator(['in_stock', 'limited', 'out_of_stock', 'discontinued'])
    lead_time_days = factory.LazyAttribute(lambda obj: random.randint(1, 90))
    specifications = factory.LazyAttribute(lambda obj: {
        'material': random.choice(['stainless_steel', 'cast_iron', 'pvc', 'brass']),
        'weight_kg': round(random.uniform(1, 500), 2),
        'dimensions': f"{random.randint(10, 200)}x{random.randint(10, 200)}x{random.randint(10, 200)}mm",
        'certifications': random.sample(['NSF', 'UL', 'CE', 'ISO9001', 'API'], k=random.randint(1, 3))
    })


class PumpFactory(ProductFactory):
    """Factory for pump-specific test data."""
    
    category = 'pump'
    flow_rate_lpm = factory.LazyAttribute(lambda obj: round(random.uniform(10, 1000), 1))
    head_meters = factory.LazyAttribute(lambda obj: round(random.uniform(5, 100), 1))
    power_kw = factory.LazyAttribute(lambda obj: round(random.uniform(0.5, 50), 2))
    efficiency_percent = factory.LazyAttribute(lambda obj: round(random.uniform(70, 95), 1))
    inlet_size = factory.Iterator(['1 inch', '2 inch', '3 inch', '4 inch', '6 inch', '8 inch'])
    outlet_size = factory.Iterator(['1 inch', '2 inch', '3 inch', '4 inch', '6 inch', '8 inch'])
    pump_type = factory.Iterator(['centrifugal', 'positive_displacement', 'submersible', 'booster'])
    
    specifications = factory.LazyAttribute(lambda obj: {
        **ProductFactory.specifications.generate({}),
        'flow_rate_lpm': obj.flow_rate_lpm,
        'head_meters': obj.head_meters,
        'power_kw': obj.power_kw,
        'efficiency_percent': obj.efficiency_percent,
        'inlet_size': obj.inlet_size,
        'outlet_size': obj.outlet_size,
        'pump_type': obj.pump_type,
        'max_temperature': random.randint(40, 120)
    })


class UVReactorFactory(ProductFactory):
    """Factory for UV reactor test data."""
    
    category = 'uv_reactor'
    flow_rate_lpm = factory.LazyAttribute(lambda obj: round(random.uniform(50, 2000), 1))
    uv_dose_mj_cm2 = factory.LazyAttribute(lambda obj: round(random.uniform(20, 100), 1))
    power_kw = factory.LazyAttribute(lambda obj: round(random.uniform(0.5, 10), 2))
    lamp_count = factory.LazyAttribute(lambda obj: random.randint(1, 20))
    lamp_type = factory.Iterator(['low_pressure', 'medium_pressure', 'amalgam'])
    reactor_material = factory.Iterator(['stainless_steel_316l', 'stainless_steel_304', 'pvc'])
    
    specifications = factory.LazyAttribute(lambda obj: {
        **ProductFactory.specifications.generate({}),
        'flow_rate_lpm': obj.flow_rate_lpm,
        'uv_dose_mj_cm2': obj.uv_dose_mj_cm2,
        'power_kw': obj.power_kw,
        'lamp_count': obj.lamp_count,
        'lamp_type': obj.lamp_type,
        'reactor_material': obj.reactor_material,
        'inlet_size': random.choice(['2 inch', '4 inch', '6 inch', '8 inch']),
        'outlet_size': random.choice(['2 inch', '4 inch', '6 inch', '8 inch'])
    })


class PriceHistoryFactory(BaseFactory):
    """Factory for price history test data."""
    
    class Meta:
        model = dict
    
    product_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    price_usd = factory.LazyAttribute(lambda obj: round(random.uniform(100, 10000), 2))
    currency = 'USD'
    supplier_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    recorded_at = factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365)))
    source = factory.Iterator(['api', 'scraping', 'manual', 'import'])
    confidence_score = factory.LazyAttribute(lambda obj: round(random.uniform(0.5, 1.0), 2))


class WorkflowExecutionFactory(BaseFactory):
    """Factory for workflow execution test data."""
    
    class Meta:
        model = dict
    
    workflow_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    workflow_type = factory.Iterator(['price_monitoring', 'data_research', 'proposal_generation', 'maintenance_scheduling'])
    status = factory.Iterator(['pending', 'running', 'completed', 'failed', 'cancelled'])
    started_at = factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)))
    completed_at = factory.LazyAttribute(lambda obj: obj.started_at + timedelta(minutes=random.randint(5, 120)) if obj.status == 'completed' else None)
    input_data = factory.LazyAttribute(lambda obj: {
        'search_terms': ['pump', 'filter'],
        'suppliers': [str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
        'budget_range': {'min': 1000, 'max': 50000}
    })
    output_data = factory.LazyAttribute(lambda obj: {
        'results_count': random.randint(0, 100),
        'processing_time_seconds': random.randint(30, 3600),
        'success_rate': round(random.uniform(0.7, 1.0), 2)
    } if obj.status == 'completed' else None)
    error_message = factory.LazyAttribute(lambda obj: 'Connection timeout' if obj.status == 'failed' else None)


class ProposalFactory(BaseFactory):
    """Factory for proposal test data."""
    
    class Meta:
        model = dict
    
    title = Faker('catch_phrase')
    description = Faker('text', max_nb_chars=500)
    customer_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    project_type = factory.Iterator(['water_treatment', 'wastewater', 'industrial', 'municipal'])
    budget_usd = factory.LazyAttribute(lambda obj: round(random.uniform(10000, 1000000), 2))
    status = factory.Iterator(['draft', 'submitted', 'under_review', 'approved', 'rejected'])
    due_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=random.randint(7, 90)))
    components = factory.LazyAttribute(lambda obj: [
        {
            'product_id': str(uuid.uuid4()),
            'quantity': random.randint(1, 10),
            'unit_price': round(random.uniform(100, 5000), 2)
        } for _ in range(random.randint(3, 15))
    ])
    total_cost = factory.LazyAttribute(lambda obj: sum(c['quantity'] * c['unit_price'] for c in obj.components))


class MaintenanceScheduleFactory(BaseFactory):
    """Factory for maintenance schedule test data."""
    
    class Meta:
        model = dict
    
    equipment_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    maintenance_type = factory.Iterator(['preventive', 'corrective', 'predictive', 'emergency'])
    priority = factory.Iterator(['low', 'medium', 'high', 'critical'])
    scheduled_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=random.randint(1, 180)))
    estimated_duration_hours = factory.LazyAttribute(lambda obj: random.randint(1, 24))
    assigned_technician = Faker('name')
    description = Faker('text', max_nb_chars=200)
    required_parts = factory.LazyAttribute(lambda obj: [
        {
            'part_id': str(uuid.uuid4()),
            'quantity': random.randint(1, 5),
            'description': f'Part {i+1}'
        } for i in range(random.randint(0, 5))
    ])
    status = factory.Iterator(['scheduled', 'in_progress', 'completed', 'cancelled', 'overdue'])


class ComplianceRecordFactory(BaseFactory):
    """Factory for compliance record test data."""
    
    class Meta:
        model = dict
    
    regulation_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    regulation_name = factory.Iterator(['EPA Clean Water Act', 'ISO 14001', 'OSHA Safety Standards', 'Local Water Quality'])
    compliance_status = factory.Iterator(['compliant', 'non_compliant', 'pending_review', 'exempt'])
    last_audit_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365)))
    next_audit_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=random.randint(30, 365)))
    auditor = Faker('name')
    findings = factory.LazyAttribute(lambda obj: [
        f'Finding {i+1}: {Faker("sentence").generate()}' 
        for i in range(random.randint(0, 5))
    ])
    corrective_actions = factory.LazyAttribute(lambda obj: [
        f'Action {i+1}: {Faker("sentence").generate()}' 
        for i in range(len(obj.findings))
    ])


class TelemetryDataFactory(BaseFactory):
    """Factory for telemetry data."""
    
    class Meta:
        model = dict
    
    device_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    timestamp = factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 1440)))
    metrics = factory.LazyAttribute(lambda obj: {
        'temperature': round(random.uniform(15, 35), 2),
        'pressure': round(random.uniform(1, 10), 2),
        'flow_rate': round(random.uniform(50, 500), 2),
        'ph_level': round(random.uniform(6.5, 8.5), 2),
        'turbidity': round(random.uniform(0, 5), 2),
        'chlorine_residual': round(random.uniform(0.2, 2.0), 2)
    })
    alerts = factory.LazyAttribute(lambda obj: [
        {
            'type': alert_type,
            'severity': random.choice(['low', 'medium', 'high']),
            'message': f'{alert_type.title()} alert triggered'
        }
        for alert_type in random.sample(['temperature', 'pressure', 'flow', 'quality'], k=random.randint(0, 2))
    ])
    location = factory.LazyAttribute(lambda obj: {
        'latitude': round(random.uniform(-90, 90), 6),
        'longitude': round(random.uniform(-180, 180), 6),
        'site_name': Faker('city').generate()
    })


class GeospatialDataFactory(BaseFactory):
    """Factory for geospatial data."""
    
    class Meta:
        model = dict
    
    location_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    latitude = factory.LazyAttribute(lambda obj: round(random.uniform(-90, 90), 6))
    longitude = factory.LazyAttribute(lambda obj: round(random.uniform(-180, 180), 6))
    address = Faker('address')
    city = Faker('city')
    state = Faker('state')
    country = Faker('country')
    postal_code = Faker('postcode')
    elevation_meters = factory.LazyAttribute(lambda obj: round(random.uniform(-100, 3000), 1))
    timezone = factory.Iterator(['UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo'])
    properties = factory.LazyAttribute(lambda obj: {
        'population': random.randint(1000, 1000000),
        'water_source': random.choice(['groundwater', 'surface_water', 'mixed']),
        'treatment_capacity': random.randint(100, 10000),
        'service_area_km2': round(random.uniform(1, 1000), 2)
    })


class ClimateDataFactory(BaseFactory):
    """Factory for climate data."""
    
    class Meta:
        model = dict
    
    location_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    date = factory.LazyFunction(lambda: datetime.now(timezone.utc).date() - timedelta(days=random.randint(0, 365)))
    temperature_celsius = factory.LazyAttribute(lambda obj: round(random.uniform(-20, 45), 1))
    humidity_percent = factory.LazyAttribute(lambda obj: round(random.uniform(20, 100), 1))
    precipitation_mm = factory.LazyAttribute(lambda obj: round(random.uniform(0, 50), 2))
    wind_speed_kmh = factory.LazyAttribute(lambda obj: round(random.uniform(0, 100), 1))
    atmospheric_pressure_hpa = factory.LazyAttribute(lambda obj: round(random.uniform(980, 1040), 1))
    uv_index = factory.LazyAttribute(lambda obj: random.randint(0, 11))
    air_quality_index = factory.LazyAttribute(lambda obj: random.randint(0, 500))
    forecast_data = factory.LazyAttribute(lambda obj: {
        'next_7_days': [
            {
                'date': (datetime.now(timezone.utc).date() + timedelta(days=i)).isoformat(),
                'temperature_high': round(random.uniform(15, 35), 1),
                'temperature_low': round(random.uniform(5, 25), 1),
                'precipitation_probability': random.randint(0, 100)
            } for i in range(1, 8)
        ]
    })


class IoTDeviceFactory(BaseFactory):
    """Factory for IoT device data."""
    
    class Meta:
        model = dict
    
    device_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    device_type = factory.Iterator(['sensor', 'actuator', 'gateway', 'controller'])
    manufacturer = factory.Iterator(['Siemens', 'Schneider Electric', 'ABB', 'Honeywell', 'Emerson'])
    model = factory.LazyAttribute(lambda obj: f"{obj.manufacturer}-{random.randint(1000, 9999)}")
    firmware_version = factory.LazyAttribute(lambda obj: f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}")
    installation_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1095)))
    last_maintenance = factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180)))
    status = factory.Iterator(['online', 'offline', 'maintenance', 'error'])
    location_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    configuration = factory.LazyAttribute(lambda obj: {
        'sampling_rate_seconds': random.choice([1, 5, 10, 30, 60]),
        'data_retention_days': random.choice([7, 30, 90, 365]),
        'alert_thresholds': {
            'temperature': {'min': 0, 'max': 50},
            'pressure': {'min': 0.5, 'max': 15}
        },
        'communication_protocol': random.choice(['MQTT', 'HTTP', 'CoAP', 'LoRaWAN'])
    })


# Utility functions for creating test data

def create_test_supplier(**kwargs) -> Dict[str, Any]:
    """Create a test supplier with optional overrides."""
    return SupplierFactory(**kwargs)


def create_test_product(category: str = None, **kwargs) -> Dict[str, Any]:
    """Create a test product with optional category and overrides."""
    if category == 'pump':
        return PumpFactory(**kwargs)
    elif category == 'uv_reactor':
        return UVReactorFactory(**kwargs)
    else:
        return ProductFactory(category=category, **kwargs)


def create_test_proposal(**kwargs) -> Dict[str, Any]:
    """Create a test proposal with optional overrides."""
    return ProposalFactory(**kwargs)


def create_test_maintenance_schedule(**kwargs) -> Dict[str, Any]:
    """Create a test maintenance schedule with optional overrides."""
    return MaintenanceScheduleFactory(**kwargs)


def create_test_compliance_record(**kwargs) -> Dict[str, Any]:
    """Create a test compliance record with optional overrides."""
    return ComplianceRecordFactory(**kwargs)


def create_test_telemetry_data(**kwargs) -> Dict[str, Any]:
    """Create test telemetry data with optional overrides."""
    return TelemetryDataFactory(**kwargs)


def create_test_workflow_execution(**kwargs) -> Dict[str, Any]:
    """Create a test workflow execution with optional overrides."""
    return WorkflowExecutionFactory(**kwargs)


def create_test_dataset(factory_class, count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """Create a list of test data objects using the specified factory."""
    return [factory_class(**kwargs) for _ in range(count)]


def create_realistic_pump_catalog(count: int = 50) -> List[Dict[str, Any]]:
    """Create a realistic pump catalog with varied specifications."""
    pumps = []
    
    # Create different pump categories
    categories = [
        {'flow_range': (10, 100), 'head_range': (5, 30), 'power_range': (0.5, 5)},  # Small pumps
        {'flow_range': (100, 500), 'head_range': (20, 60), 'power_range': (2, 15)},  # Medium pumps
        {'flow_range': (500, 2000), 'head_range': (40, 100), 'power_range': (10, 50)}  # Large pumps
    ]
    
    for i in range(count):
        category = random.choice(categories)
        pump = PumpFactory(
            flow_rate_lpm=round(random.uniform(*category['flow_range']), 1),
            head_meters=round(random.uniform(*category['head_range']), 1),
            power_kw=round(random.uniform(*category['power_range']), 2)
        )
        pumps.append(pump)
    
    return pumps


def create_realistic_uv_catalog(count: int = 30) -> List[Dict[str, Any]]:
    """Create a realistic UV reactor catalog with varied specifications."""
    uv_reactors = []
    
    # Create different UV reactor categories
    categories = [
        {'flow_range': (50, 300), 'dose_range': (20, 40), 'power_range': (0.5, 3)},  # Small UV
        {'flow_range': (300, 1000), 'dose_range': (30, 60), 'power_range': (2, 8)},  # Medium UV
        {'flow_range': (1000, 5000), 'dose_range': (40, 100), 'power_range': (5, 20)}  # Large UV
    ]
    
    for i in range(count):
        category = random.choice(categories)
        uv_reactor = UVReactorFactory(
            flow_rate_lpm=round(random.uniform(*category['flow_range']), 1),
            uv_dose_mj_cm2=round(random.uniform(*category['dose_range']), 1),
            power_kw=round(random.uniform(*category['power_range']), 2)
        )
        uv_reactors.append(uv_reactor)
    
    return uv_reactors