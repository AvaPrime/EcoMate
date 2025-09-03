"""Database fixtures and mock data for testing."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.models import Base, Product, PriceHistory, Supplier, WorkflowExecution, User
from src.database.connection import DatabaseManager


@pytest.fixture(scope="session")
def test_database_url():
    """Create in-memory SQLite database URL for testing."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Create test database engine."""
    engine = create_engine(
        test_database_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine, test_session_factory):
    """Create test database session with automatic cleanup."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = test_session_factory()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables for clean state
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def mock_database_manager():
    """Create a mock database manager for testing."""
    manager = Mock(spec=DatabaseManager)
    
    # Mock session context manager
    mock_session = Mock(spec=Session)
    manager.get_session.return_value.__enter__.return_value = mock_session
    manager.get_session.return_value.__exit__.return_value = None
    
    # Configure mock session methods
    mock_session.query.return_value = mock_session
    mock_session.filter.return_value = mock_session
    mock_session.filter_by.return_value = mock_session
    mock_session.order_by.return_value = mock_session
    mock_session.limit.return_value = mock_session
    mock_session.offset.return_value = mock_session
    mock_session.first.return_value = None
    mock_session.all.return_value = []
    mock_session.count.return_value = 0
    mock_session.add.return_value = None
    mock_session.add_all.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.delete.return_value = None
    mock_session.merge.return_value = None
    
    return manager


@pytest.fixture
def sample_users():
    """Create sample user data for testing."""
    return [
        User(
            id=1,
            username="testuser1",
            email="testuser1@example.com",
            full_name="Test User One",
            is_active=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=30),
            updated_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        User(
            id=2,
            username="testuser2",
            email="testuser2@example.com",
            full_name="Test User Two",
            is_active=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=15),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=6)
        ),
        User(
            id=3,
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
    ]


@pytest.fixture
def sample_suppliers_db():
    """Create sample supplier database records for testing."""
    return [
        Supplier(
            id=1,
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
            lead_time_days=14,
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=90),
            updated_at=datetime.now(timezone.utc) - timedelta(days=5)
        ),
        Supplier(
            id=2,
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
            lead_time_days=21,
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=75),
            updated_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Supplier(
            id=3,
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
            lead_time_days=45,
            is_active=False,  # Inactive supplier for testing
            created_at=datetime.now(timezone.utc) - timedelta(days=120),
            updated_at=datetime.now(timezone.utc) - timedelta(days=30)
        )
    ]


@pytest.fixture
def sample_products_db(sample_suppliers_db):
    """Create sample product database records for testing."""
    return [
        Product(
            id=1,
            name="AquaTech Centrifugal Pump CP-100",
            category="pumps",
            price=Decimal("1500.00"),
            currency="USD",
            url="https://aquatech-solutions.com/centrifugal-pump-cp-100",
            supplier_id=1,
            specifications={
                "flow_rate": 100,
                "head_pressure": 45,
                "power_consumption": 750,
                "inlet_size": "4 inches",
                "outlet_size": "3 inches",
                "material": "stainless steel",
                "certifications": ["NSF", "UL"],
                "efficiency_rating": 85.5
            },
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
            ],
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
            updated_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        Product(
            id=2,
            name="WaterTech Pro UV Reactor UV-55R",
            category="uv_reactors",
            price=Decimal("850.00"),
            currency="USD",
            url="https://watertech-pro.com/uv-reactor-uv-55r",
            supplier_id=2,
            specifications={
                "uv_dose": 40,
                "flow_rate": 10,
                "lamp_power": 55,
                "lamp_type": "low pressure",
                "reactor_material": "stainless steel 316L",
                "certifications": ["NSF 55", "DVGW"],
                "lamp_life_hours": 9000
            },
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
            ],
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=12)
        ),
        Product(
            id=3,
            name="AquaTech Industrial UV System UV-1200I",
            category="uv_reactors",
            price=Decimal("12500.00"),
            currency="USD",
            url="https://aquatech-solutions.com/uv-system-uv-1200i",
            supplier_id=1,
            specifications={
                "uv_dose": 40,
                "flow_rate": 500,
                "lamp_power": 1200,
                "lamp_type": "amalgam",
                "reactor_material": "stainless steel 316L",
                "certifications": ["NSF 55", "USEPA", "DVGW", "WRAS"],
                "lamp_life_hours": 16000
            },
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
            ],
            created_at=datetime.now(timezone.utc) - timedelta(days=30),
            updated_at=datetime.now(timezone.utc) - timedelta(days=7)
        )
    ]


@pytest.fixture
def sample_price_history_db():
    """Create sample price history database records for testing."""
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    return [
        # Product 1 price history (increasing trend)
        PriceHistory(
            id=1,
            product_id=1,
            price=Decimal("1450.00"),
            currency="USD",
            recorded_at=base_date,
            supplier="AquaTech Solutions",
            availability=True,
            source_url="https://aquatech-solutions.com/centrifugal-pump-cp-100"
        ),
        PriceHistory(
            id=2,
            product_id=1,
            price=Decimal("1475.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=7),
            supplier="AquaTech Solutions",
            availability=True,
            source_url="https://aquatech-solutions.com/centrifugal-pump-cp-100"
        ),
        PriceHistory(
            id=3,
            product_id=1,
            price=Decimal("1500.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=14),
            supplier="AquaTech Solutions",
            availability=True,
            source_url="https://aquatech-solutions.com/centrifugal-pump-cp-100"
        ),
        PriceHistory(
            id=4,
            product_id=1,
            price=Decimal("1525.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=21),
            supplier="AquaTech Solutions",
            availability=True,
            source_url="https://aquatech-solutions.com/centrifugal-pump-cp-100"
        ),
        PriceHistory(
            id=5,
            product_id=1,
            price=Decimal("1600.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=28),
            supplier="AquaTech Solutions",
            availability=True,
            source_url="https://aquatech-solutions.com/centrifugal-pump-cp-100"
        ),
        # Product 2 price history (decreasing trend)
        PriceHistory(
            id=6,
            product_id=2,
            price=Decimal("900.00"),
            currency="USD",
            recorded_at=base_date,
            supplier="WaterTech Pro",
            availability=True,
            source_url="https://watertech-pro.com/uv-reactor-uv-55r"
        ),
        PriceHistory(
            id=7,
            product_id=2,
            price=Decimal("875.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=7),
            supplier="WaterTech Pro",
            availability=True,
            source_url="https://watertech-pro.com/uv-reactor-uv-55r"
        ),
        PriceHistory(
            id=8,
            product_id=2,
            price=Decimal("850.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=14),
            supplier="WaterTech Pro",
            availability=True,
            source_url="https://watertech-pro.com/uv-reactor-uv-55r"
        ),
        # Product 3 price history (stable with availability changes)
        PriceHistory(
            id=9,
            product_id=3,
            price=Decimal("12500.00"),
            currency="USD",
            recorded_at=base_date,
            supplier="AquaTech Solutions",
            availability=True,
            source_url="https://aquatech-solutions.com/uv-system-uv-1200i"
        ),
        PriceHistory(
            id=10,
            product_id=3,
            price=Decimal("12500.00"),
            currency="USD",
            recorded_at=base_date + timedelta(days=14),
            supplier="AquaTech Solutions",
            availability=False,  # Became unavailable
            source_url="https://aquatech-solutions.com/uv-system-uv-1200i"
        )
    ]


@pytest.fixture
def sample_workflow_executions_db():
    """Create sample workflow execution database records for testing."""
    return [
        WorkflowExecution(
            id=1,
            workflow_id="research-workflow-123",
            workflow_type="research",
            status="completed",
            user_id=1,
            started_at=datetime.now(timezone.utc) - timedelta(hours=2),
            completed_at=datetime.now(timezone.utc) - timedelta(hours=1, minutes=45),
            input_data={
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
            result_data={
                "products_found": 2,
                "report_generated": True,
                "report_url": "https://reports.ecomate.com/report-123"
            },
            error_details=None
        ),
        WorkflowExecution(
            id=2,
            workflow_id="price-monitoring-456",
            workflow_type="price_monitoring",
            status="running",
            user_id=2,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            completed_at=None,
            input_data={
                "product_ids": [1, 2, 3],
                "monitoring_frequency": "daily",
                "price_change_threshold": 5.0
            },
            result_data=None,
            error_details=None
        ),
        WorkflowExecution(
            id=3,
            workflow_id="research-workflow-789",
            workflow_type="research",
            status="failed",
            user_id=1,
            started_at=datetime.now(timezone.utc) - timedelta(hours=1),
            completed_at=datetime.now(timezone.utc) - timedelta(minutes=45),
            input_data={
                "product_urls": ["https://invalid-url.com/product"],
                "categories": ["pumps"]
            },
            result_data=None,
            error_details={
                "error_type": "ScrapingError",
                "error_message": "Failed to scrape product data",
                "failed_urls": ["https://invalid-url.com/product"]
            }
        )
    ]


@pytest.fixture
def database_test_data(test_db_session, sample_users, sample_suppliers_db, sample_products_db, sample_price_history_db, sample_workflow_executions_db):
    """Populate test database with sample data."""
    # Add users
    for user in sample_users:
        test_db_session.add(user)
    
    # Add suppliers
    for supplier in sample_suppliers_db:
        test_db_session.add(supplier)
    
    # Add products
    for product in sample_products_db:
        test_db_session.add(product)
    
    # Add price history
    for price_record in sample_price_history_db:
        test_db_session.add(price_record)
    
    # Add workflow executions
    for workflow in sample_workflow_executions_db:
        test_db_session.add(workflow)
    
    test_db_session.commit()
    
    return {
        "users": sample_users,
        "suppliers": sample_suppliers_db,
        "products": sample_products_db,
        "price_history": sample_price_history_db,
        "workflow_executions": sample_workflow_executions_db
    }


@pytest.fixture
def database_query_scenarios():
    """Create database query scenarios for testing."""
    return {
        "product_queries": [
            {"category": "pumps", "expected_count": 1},
            {"category": "uv_reactors", "expected_count": 2},
            {"availability": True, "expected_count": 2},
            {"availability": False, "expected_count": 1},
            {"price_min": Decimal("1000.00"), "expected_count": 2},
            {"price_max": Decimal("1000.00"), "expected_count": 1}
        ],
        "supplier_queries": [
            {"is_active": True, "expected_count": 2},
            {"is_active": False, "expected_count": 1},
            {"specialties_contains": "pumps", "expected_count": 2},
            {"specialties_contains": "uv_reactors", "expected_count": 1}
        ],
        "price_history_queries": [
            {"product_id": 1, "expected_count": 5},
            {"product_id": 2, "expected_count": 3},
            {"product_id": 3, "expected_count": 2},
            {"date_range": {"start": datetime.now(timezone.utc) - timedelta(days=20), "end": datetime.now(timezone.utc)}, "expected_count": 4}
        ],
        "workflow_queries": [
            {"status": "completed", "expected_count": 1},
            {"status": "running", "expected_count": 1},
            {"status": "failed", "expected_count": 1},
            {"workflow_type": "research", "expected_count": 2},
            {"workflow_type": "price_monitoring", "expected_count": 1}
        ]
    }


@pytest.fixture
def database_performance_scenarios():
    """Create database performance testing scenarios."""
    return {
        "bulk_insert_scenarios": [
            {"table": "products", "record_count": 100},
            {"table": "price_history", "record_count": 1000},
            {"table": "workflow_executions", "record_count": 50}
        ],
        "complex_query_scenarios": [
            {
                "name": "products_with_recent_price_changes",
                "description": "Find products with price changes in last 7 days",
                "expected_execution_time_ms": 100
            },
            {
                "name": "supplier_performance_report",
                "description": "Generate supplier performance metrics",
                "expected_execution_time_ms": 200
            },
            {
                "name": "workflow_success_rate",
                "description": "Calculate workflow success rates by type",
                "expected_execution_time_ms": 150
            }
        ],
        "concurrent_access_scenarios": [
            {"concurrent_reads": 10, "concurrent_writes": 2},
            {"concurrent_reads": 20, "concurrent_writes": 5},
            {"concurrent_reads": 50, "concurrent_writes": 10}
        ]
    }


@pytest.fixture
def database_migration_scenarios():
    """Create database migration testing scenarios."""
    return {
        "schema_changes": [
            {
                "migration_name": "add_product_rating_column",
                "description": "Add rating column to products table",
                "sql_up": "ALTER TABLE products ADD COLUMN rating DECIMAL(3,2);",
                "sql_down": "ALTER TABLE products DROP COLUMN rating;"
            },
            {
                "migration_name": "add_supplier_contact_person",
                "description": "Add contact person to suppliers table",
                "sql_up": "ALTER TABLE suppliers ADD COLUMN contact_person VARCHAR(255);",
                "sql_down": "ALTER TABLE suppliers DROP COLUMN contact_person;"
            }
        ],
        "data_migrations": [
            {
                "migration_name": "normalize_phone_numbers",
                "description": "Normalize phone number format in suppliers table",
                "test_data": [
                    {"old_format": "555-0123", "new_format": "+1-555-0123"},
                    {"old_format": "(555) 456-7890", "new_format": "+1-555-456-7890"}
                ]
            }
        ]
    }


@pytest.fixture
def database_error_scenarios():
    """Create database error scenarios for testing."""
    return {
        "connection_errors": [
            {"error_type": "connection_timeout", "expected_exception": "sqlalchemy.exc.TimeoutError"},
            {"error_type": "connection_refused", "expected_exception": "sqlalchemy.exc.OperationalError"},
            {"error_type": "invalid_credentials", "expected_exception": "sqlalchemy.exc.OperationalError"}
        ],
        "constraint_violations": [
            {"violation_type": "unique_constraint", "table": "users", "column": "email"},
            {"violation_type": "foreign_key_constraint", "table": "products", "column": "supplier_id"},
            {"violation_type": "not_null_constraint", "table": "products", "column": "name"}
        ],
        "transaction_errors": [
            {"error_type": "deadlock", "expected_exception": "sqlalchemy.exc.OperationalError"},
            {"error_type": "rollback_required", "expected_exception": "sqlalchemy.exc.InvalidRequestError"}
        ]
    }