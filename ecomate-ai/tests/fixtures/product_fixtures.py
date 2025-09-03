"""Product-related test fixtures and mock data."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from src.models.product import ProductBase, PumpSpecification, UVReactorSpecification
from src.models.supplier import Supplier


@pytest.fixture
def sample_pump_specifications():
    """Create sample pump specifications for testing."""
    return {
        "basic_pump": PumpSpecification(
            flow_rate=100,
            head_pressure=45,
            power_consumption=750,
            inlet_size="4 inches",
            outlet_size="3 inches",
            material="stainless steel",
            certifications=["NSF", "UL"],
            efficiency_rating=85.5,
            operating_temperature_range="5-40°C",
            maximum_solids_size="3mm"
        ),
        "high_capacity_pump": PumpSpecification(
            flow_rate=250,
            head_pressure=80,
            power_consumption=1500,
            inlet_size="8 inches",
            outlet_size="6 inches",
            material="duplex stainless steel",
            certifications=["API", "ASME", "ISO 9001"],
            efficiency_rating=92.0,
            operating_temperature_range="-10-60°C",
            maximum_solids_size="5mm"
        ),
        "compact_pump": PumpSpecification(
            flow_rate=50,
            head_pressure=25,
            power_consumption=375,
            inlet_size="2 inches",
            outlet_size="1.5 inches",
            material="cast iron",
            certifications=["NSF"],
            efficiency_rating=78.0,
            operating_temperature_range="0-50°C",
            maximum_solids_size="1mm"
        )
    }


@pytest.fixture
def sample_uv_reactor_specifications():
    """Create sample UV reactor specifications for testing."""
    return {
        "residential_uv": UVReactorSpecification(
            uv_dose=40,
            flow_rate=10,
            lamp_power=55,
            lamp_type="low pressure",
            reactor_material="stainless steel 316L",
            certifications=["NSF 55", "DVGW"],
            lamp_life_hours=9000,
            operating_pressure_range="1-8 bar",
            water_temperature_range="2-40°C"
        ),
        "commercial_uv": UVReactorSpecification(
            uv_dose=40,
            flow_rate=100,
            lamp_power=320,
            lamp_type="medium pressure",
            reactor_material="stainless steel 316L",
            certifications=["NSF 55", "USEPA", "Health Canada"],
            lamp_life_hours=12000,
            operating_pressure_range="2-10 bar",
            water_temperature_range="2-60°C"
        ),
        "industrial_uv": UVReactorSpecification(
            uv_dose=40,
            flow_rate=500,
            lamp_power=1200,
            lamp_type="amalgam",
            reactor_material="stainless steel 316L",
            certifications=["NSF 55", "USEPA", "DVGW", "WRAS"],
            lamp_life_hours=16000,
            operating_pressure_range="3-16 bar",
            water_temperature_range="2-85°C"
        )
    }


@pytest.fixture
def sample_suppliers():
    """Create sample supplier data for testing."""
    return {
        "aquatech_solutions": Supplier(
            name="AquaTech Solutions",
            website="https://aquatech-solutions.com",
            contact_email="sales@aquatech-solutions.com",
            phone="+1-555-0123",
            address="123 Industrial Blvd, Water City, WC 12345",
            specialties=["pumps", "filtration", "water treatment"],
            certifications=["ISO 9001", "ISO 14001"],
            payment_terms="Net 30",
            shipping_regions=["North America", "Europe"],
            minimum_order_value=Decimal("500.00"),
            lead_time_days=14
        ),
        "watertech_pro": Supplier(
            name="WaterTech Pro",
            website="https://watertech-pro.com",
            contact_email="info@watertech-pro.com",
            phone="+1-555-0456",
            address="456 Tech Park Dr, Innovation City, IC 67890",
            specialties=["uv_reactors", "disinfection", "monitoring"],
            certifications=["NSF", "ANSI", "UL"],
            payment_terms="Net 45",
            shipping_regions=["Worldwide"],
            minimum_order_value=Decimal("1000.00"),
            lead_time_days=21
        ),
        "industrial_pumps_inc": Supplier(
            name="Industrial Pumps Inc",
            website="https://industrial-pumps.com",
            contact_email="orders@industrial-pumps.com",
            phone="+1-555-0789",
            address="789 Heavy Industry Ave, Manufacturing Town, MT 13579",
            specialties=["heavy_duty_pumps", "industrial_equipment"],
            certifications=["API", "ASME", "OSHA"],
            payment_terms="Net 60",
            shipping_regions=["North America"],
            minimum_order_value=Decimal("2000.00"),
            lead_time_days=45
        )
    }


@pytest.fixture
def sample_products(sample_pump_specifications, sample_uv_reactor_specifications, sample_suppliers):
    """Create sample product data for testing."""
    return {
        "centrifugal_pump_cp100": ProductBase(
            name="AquaTech Centrifugal Pump CP-100",
            category="pumps",
            price=Decimal("1500.00"),
            currency="USD",
            url="https://aquatech-solutions.com/centrifugal-pump-cp-100",
            supplier=sample_suppliers["aquatech_solutions"],
            specifications=sample_pump_specifications["basic_pump"],
            description="High-efficiency centrifugal pump for water treatment applications",
            model_number="CP-100",
            availability=True,
            lead_time_days=14,
            warranty_years=2,
            images=[
                "https://aquatech-solutions.com/images/cp-100-front.jpg",
                "https://aquatech-solutions.com/images/cp-100-specs.jpg"
            ],
            documents=[
                "https://aquatech-solutions.com/docs/cp-100-manual.pdf",
                "https://aquatech-solutions.com/docs/cp-100-datasheet.pdf"
            ]
        ),
        "high_flow_pump_hf200": ProductBase(
            name="WaterTech Pro High-Flow Pump HF-200",
            category="pumps",
            price=Decimal("1800.00"),
            currency="USD",
            url="https://watertech-pro.com/high-flow-pump-hf-200",
            supplier=sample_suppliers["watertech_pro"],
            specifications=sample_pump_specifications["high_capacity_pump"],
            description="High-capacity pump for large-scale water treatment facilities",
            model_number="HF-200",
            availability=True,
            lead_time_days=21,
            warranty_years=3,
            images=[
                "https://watertech-pro.com/images/hf-200-main.jpg"
            ],
            documents=[
                "https://watertech-pro.com/docs/hf-200-installation.pdf"
            ]
        ),
        "residential_uv_reactor": ProductBase(
            name="WaterTech Pro UV Reactor UV-55R",
            category="uv_reactors",
            price=Decimal("850.00"),
            currency="USD",
            url="https://watertech-pro.com/uv-reactor-uv-55r",
            supplier=sample_suppliers["watertech_pro"],
            specifications=sample_uv_reactor_specifications["residential_uv"],
            description="Compact UV disinfection system for residential applications",
            model_number="UV-55R",
            availability=True,
            lead_time_days=7,
            warranty_years=5,
            images=[
                "https://watertech-pro.com/images/uv-55r-system.jpg",
                "https://watertech-pro.com/images/uv-55r-installation.jpg"
            ],
            documents=[
                "https://watertech-pro.com/docs/uv-55r-manual.pdf",
                "https://watertech-pro.com/docs/uv-55r-certification.pdf"
            ]
        ),
        "industrial_uv_reactor": ProductBase(
            name="AquaTech Industrial UV System UV-1200I",
            category="uv_reactors",
            price=Decimal("12500.00"),
            currency="USD",
            url="https://aquatech-solutions.com/uv-system-uv-1200i",
            supplier=sample_suppliers["aquatech_solutions"],
            specifications=sample_uv_reactor_specifications["industrial_uv"],
            description="High-capacity UV disinfection system for industrial applications",
            model_number="UV-1200I",
            availability=False,
            lead_time_days=60,
            warranty_years=3,
            images=[
                "https://aquatech-solutions.com/images/uv-1200i-system.jpg"
            ],
            documents=[
                "https://aquatech-solutions.com/docs/uv-1200i-technical.pdf",
                "https://aquatech-solutions.com/docs/uv-1200i-compliance.pdf"
            ]
        )
    }


@pytest.fixture
def sample_price_history():
    """Create sample price history data for testing."""
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    return {
        "product_1_history": [
            {
                "product_id": 1,
                "price": Decimal("1450.00"),
                "currency": "USD",
                "recorded_at": base_date,
                "supplier": "AquaTech Solutions",
                "availability": True
            },
            {
                "product_id": 1,
                "price": Decimal("1475.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=7),
                "supplier": "AquaTech Solutions",
                "availability": True
            },
            {
                "product_id": 1,
                "price": Decimal("1500.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=14),
                "supplier": "AquaTech Solutions",
                "availability": True
            },
            {
                "product_id": 1,
                "price": Decimal("1525.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=21),
                "supplier": "AquaTech Solutions",
                "availability": True
            },
            {
                "product_id": 1,
                "price": Decimal("1600.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=28),
                "supplier": "AquaTech Solutions",
                "availability": True
            }
        ],
        "product_2_history": [
            {
                "product_id": 2,
                "price": Decimal("1850.00"),
                "currency": "USD",
                "recorded_at": base_date,
                "supplier": "WaterTech Pro",
                "availability": True
            },
            {
                "product_id": 2,
                "price": Decimal("1825.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=7),
                "supplier": "WaterTech Pro",
                "availability": True
            },
            {
                "product_id": 2,
                "price": Decimal("1800.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=14),
                "supplier": "WaterTech Pro",
                "availability": True
            },
            {
                "product_id": 2,
                "price": Decimal("1775.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=21),
                "supplier": "WaterTech Pro",
                "availability": True
            },
            {
                "product_id": 2,
                "price": Decimal("1750.00"),
                "currency": "USD",
                "recorded_at": base_date + timedelta(days=28),
                "supplier": "WaterTech Pro",
                "availability": True
            }
        ]
    }


@pytest.fixture
def sample_workflow_executions():
    """Create sample workflow execution data for testing."""
    return {
        "research_workflow_success": {
            "workflow_id": "research-workflow-123",
            "workflow_type": "research",
            "status": "completed",
            "user_id": "user-123",
            "started_at": datetime.now(timezone.utc) - timedelta(hours=2),
            "completed_at": datetime.now(timezone.utc) - timedelta(hours=1, minutes=45),
            "input_data": {
                "product_urls": [
                    "https://example.com/pump1",
                    "https://example.com/pump2"
                ],
                "categories": ["pumps"],
                "research_criteria": {
                    "max_price": 2000,
                    "min_flow_rate": 50
                }
            },
            "result_data": {
                "products_found": 2,
                "report_generated": True,
                "report_url": "https://reports.ecomate.com/report-123"
            },
            "error_details": None
        },
        "price_monitoring_workflow_success": {
            "workflow_id": "price-monitoring-456",
            "workflow_type": "price_monitoring",
            "status": "completed",
            "user_id": "user-456",
            "started_at": datetime.now(timezone.utc) - timedelta(minutes=30),
            "completed_at": datetime.now(timezone.utc) - timedelta(minutes=25),
            "input_data": {
                "product_ids": [1, 2, 3],
                "monitoring_frequency": "daily",
                "price_change_threshold": 5.0
            },
            "result_data": {
                "products_monitored": 3,
                "significant_changes": 1,
                "alerts_sent": 1
            },
            "error_details": None
        },
        "research_workflow_failed": {
            "workflow_id": "research-workflow-789",
            "workflow_type": "research",
            "status": "failed",
            "user_id": "user-789",
            "started_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "completed_at": datetime.now(timezone.utc) - timedelta(minutes=45),
            "input_data": {
                "product_urls": ["https://invalid-url.com/product"],
                "categories": ["pumps"]
            },
            "result_data": None,
            "error_details": {
                "error_type": "ScrapingError",
                "error_message": "Failed to scrape product data",
                "failed_urls": ["https://invalid-url.com/product"]
            }
        }
    }


@pytest.fixture
def sample_scraped_html_content():
    """Create sample HTML content for scraping tests."""
    return {
        "pump_product_page": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AquaTech Centrifugal Pump CP-100</title>
            <meta name="description" content="High-efficiency centrifugal pump for water treatment">
        </head>
        <body>
            <div class="product-container">
                <h1 class="product-title">AquaTech Centrifugal Pump CP-100</h1>
                <div class="price-section">
                    <span class="price">$1,500.00</span>
                    <span class="currency">USD</span>
                </div>
                <div class="specifications">
                    <table class="spec-table">
                        <tr><td>Flow Rate</td><td>100 GPM</td></tr>
                        <tr><td>Head Pressure</td><td>45 PSI</td></tr>
                        <tr><td>Power</td><td>750W</td></tr>
                        <tr><td>Material</td><td>Stainless Steel</td></tr>
                        <tr><td>Certifications</td><td>NSF, UL</td></tr>
                    </table>
                </div>
                <div class="availability">
                    <span class="status in-stock">In Stock</span>
                    <span class="lead-time">Ships in 14 days</span>
                </div>
                <div class="images">
                    <img src="/images/cp-100-front.jpg" alt="Front view">
                    <img src="/images/cp-100-specs.jpg" alt="Specifications">
                </div>
            </div>
        </body>
        </html>
        """,
        "uv_reactor_product_page": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WaterTech Pro UV Reactor UV-55R</title>
        </head>
        <body>
            <div class="product-info">
                <h1>WaterTech Pro UV Reactor UV-55R</h1>
                <div class="pricing">
                    <div class="price-display">$850.00</div>
                </div>
                <div class="product-specs">
                    <ul class="spec-list">
                        <li>UV Dose: 40 mJ/cm²</li>
                        <li>Flow Rate: 10 GPM</li>
                        <li>Lamp Power: 55W</li>
                        <li>Lamp Type: Low Pressure</li>
                        <li>Material: Stainless Steel 316L</li>
                    </ul>
                </div>
                <div class="stock-info">
                    <span class="availability-status">Available</span>
                    <span class="shipping-time">7 day lead time</span>
                </div>
            </div>
        </body>
        </html>
        """,
        "supplier_listing_page": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Water Treatment Equipment - AquaTech Solutions</title>
        </head>
        <body>
            <div class="product-grid">
                <div class="product-card">
                    <h3><a href="/centrifugal-pump-cp-100">Centrifugal Pump CP-100</a></h3>
                    <span class="price">$1,500.00</span>
                </div>
                <div class="product-card">
                    <h3><a href="/submersible-pump-sp-200">Submersible Pump SP-200</a></h3>
                    <span class="price">$2,200.00</span>
                </div>
                <div class="product-card">
                    <h3><a href="/uv-system-uv-1200i">UV System UV-1200I</a></h3>
                    <span class="price">$12,500.00</span>
                </div>
            </div>
        </body>
        </html>
        """
    }


@pytest.fixture
def sample_api_responses():
    """Create sample API response data for testing."""
    return {
        "successful_scraping_response": {
            "status": "success",
            "products_found": 2,
            "products": [
                {
                    "name": "AquaTech Centrifugal Pump CP-100",
                    "price": 1500.00,
                    "currency": "USD",
                    "url": "https://aquatech-solutions.com/centrifugal-pump-cp-100",
                    "specifications": {
                        "flow_rate": 100,
                        "head_pressure": 45,
                        "power_consumption": 750
                    }
                },
                {
                    "name": "WaterTech Pro High-Flow Pump HF-200",
                    "price": 1800.00,
                    "currency": "USD",
                    "url": "https://watertech-pro.com/high-flow-pump-hf-200",
                    "specifications": {
                        "flow_rate": 150,
                        "head_pressure": 60,
                        "power_consumption": 1100
                    }
                }
            ],
            "scraping_time": "2024-01-15T10:30:00Z"
        },
        "failed_scraping_response": {
            "status": "error",
            "error_code": "SCRAPING_FAILED",
            "error_message": "Unable to access product page",
            "failed_urls": [
                "https://unavailable-site.com/product"
            ],
            "retry_count": 3,
            "timestamp": "2024-01-15T10:35:00Z"
        },
        "workflow_status_response": {
            "workflow_id": "research-workflow-123",
            "status": "running",
            "progress": {
                "current_step": "scraping_products",
                "completed_steps": ["validate_input", "initialize_workflow"],
                "total_steps": 5,
                "percentage_complete": 40
            },
            "estimated_completion": "2024-01-15T11:00:00Z",
            "started_at": "2024-01-15T10:30:00Z"
        }
    }


@pytest.fixture
def mock_database_session():
    """Create a mock database session for testing."""
    session = Mock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def mock_temporal_client():
    """Create a mock Temporal client for testing."""
    client = Mock()
    client.start_workflow.return_value = Mock(
        id="test-workflow-123",
        result_run_id="run-456"
    )
    client.get_workflow_handle.return_value = Mock(
        result=Mock(return_value={"status": "completed"})
    )
    return client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    redis_client = Mock()
    redis_client.get.return_value = None
    redis_client.set.return_value = True
    redis_client.delete.return_value = 1
    redis_client.exists.return_value = False
    redis_client.expire.return_value = True
    redis_client.flushdb.return_value = True
    return redis_client


@pytest.fixture
def mock_minio_client():
    """Create a mock MinIO client for testing."""
    minio_client = Mock()
    minio_client.bucket_exists.return_value = True
    minio_client.make_bucket.return_value = None
    minio_client.put_object.return_value = Mock(etag="test-etag")
    minio_client.get_object.return_value = Mock(
        read=Mock(return_value=b"test file content")
    )
    minio_client.remove_object.return_value = None
    minio_client.list_objects.return_value = []
    return minio_client