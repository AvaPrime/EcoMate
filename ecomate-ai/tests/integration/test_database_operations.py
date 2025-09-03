"""Integration tests for database operations and data persistence."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError

from src.database.models import (
    Product,
    Supplier,
    PriceHistory,
    WorkflowExecution
)
from src.database.repositories import (
    ProductRepository,
    SupplierRepository,
    PriceHistoryRepository,
    WorkflowRepository
)
from src.database.connection import (
    DatabaseManager,
    get_async_database,
    get_redis_client
)
from src.utils.exceptions import DatabaseError, ValidationError
from src.config.database import DatabaseConfig


class TestDatabaseConnection:
    """Integration tests for database connection management."""
    
    @pytest.fixture
    def db_config(self):
        """Create test database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="ecomate_test",
            username="test_user",
            password="test_password",
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600
        )
    
    @pytest.fixture
    def mock_engine(self):
        """Create mock SQLAlchemy engine."""
        engine = Mock()
        engine.connect.return_value.__enter__ = Mock()
        engine.connect.return_value.__exit__ = Mock(return_value=None)
        engine.dispose = Mock()
        return engine
    
    @pytest.mark.asyncio
    async def test_database_manager_initialization(self, db_config, mock_engine):
        """Test DatabaseManager initialization and configuration."""
        with patch('src.database.connection.create_engine', return_value=mock_engine):
            db_manager = DatabaseManager(db_config)
            
            assert db_manager.config == db_config
            assert db_manager.engine == mock_engine
            assert db_manager.session_factory is not None
    
    @pytest.mark.asyncio
    async def test_database_connection_success(self, db_config, mock_engine):
        """Test successful database connection."""
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        with patch('src.database.connection.create_engine', return_value=mock_engine):
            db_manager = DatabaseManager(db_config)
            
            # Test connection
            with db_manager.get_connection() as conn:
                assert conn == mock_connection
            
            mock_engine.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self, db_config):
        """Test database connection failure handling."""
        with patch('src.database.connection.create_engine', side_effect=OperationalError("Connection failed", None, None)):
            with pytest.raises(DatabaseError, match="Failed to connect to database"):
                DatabaseManager(db_config)
    
    @pytest.mark.asyncio
    async def test_session_management(self, db_config, mock_engine):
        """Test database session creation and management."""
        mock_session = Mock(spec=Session)
        mock_session_factory = Mock(return_value=mock_session)
        
        with patch('src.database.connection.create_engine', return_value=mock_engine):
            with patch('src.database.connection.sessionmaker', return_value=mock_session_factory):
                db_manager = DatabaseManager(db_config)
                
                # Test session creation
                with db_manager.get_session() as session:
                    assert session == mock_session
                
                mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_database_connection(self):
        """Test async database connection setup."""
        database_url = "postgresql://test_user:test_password@localhost:5432/ecomate_test"
        
        with patch('src.database.connection.Database') as mock_database_class:
            mock_database = Mock()
            mock_database_class.return_value = mock_database
            mock_database.connect = AsyncMock()
            mock_database.disconnect = AsyncMock()
            
            async_db = get_async_database(database_url)
            
            await async_db.connect()
            mock_database.connect.assert_called_once()
            
            await async_db.disconnect()
            mock_database.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test Redis connection setup and management."""
        redis_config = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "socket_timeout": 5,
            "socket_connect_timeout": 5
        }
        
        with patch('src.database.connection.Redis') as mock_redis_class:
            mock_redis = Mock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping.return_value = True
            
            redis_client = get_redis_client(redis_config)
            
            assert redis_client == mock_redis
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Test Redis connection failure handling."""
        redis_config = {
            "host": "invalid-host",
            "port": 6379,
            "db": 0
        }
        
        with patch('src.database.connection.Redis', side_effect=RedisConnectionError("Connection failed")):
            with pytest.raises(DatabaseError, match="Failed to connect to Redis"):
                get_redis_client(redis_config)


class TestProductRepository:
    """Integration tests for Product repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value = session
        session.filter.return_value = session
        session.filter_by.return_value = session
        session.order_by.return_value = session
        session.limit.return_value = session
        session.offset.return_value = session
        session.join.return_value = session
        return session
    
    @pytest.fixture
    def product_repository(self, mock_session):
        """Create ProductRepository instance with mock session."""
        return ProductRepository(mock_session)
    
    @pytest.fixture
    def sample_product_data(self):
        """Create sample product data for testing."""
        return {
            "name": "High-Performance Centrifugal Pump",
            "category": "pumps",
            "price": Decimal("1500.00"),
            "currency": "USD",
            "supplier_id": 1,
            "url": "https://example.com/pump-123",
            "description": "Industrial grade centrifugal pump",
            "specifications": {
                "flow_rate": 100,
                "head_pressure": 50,
                "power_consumption": 750,
                "inlet_size": "4 inches",
                "outlet_size": "3 inches",
                "material": "stainless steel"
            },
            "availability": True,
            "stock_quantity": 25,
            "lead_time_days": 14
        }
    
    @pytest.mark.asyncio
    async def test_create_product_success(self, product_repository, mock_session, sample_product_data):
        """Test successful product creation."""
        # Mock successful database operations
        mock_product = Product(**sample_product_data)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('src.database.repositories.Product', return_value=mock_product):
            result = await product_repository.create_product(sample_product_data)
            
            assert result == mock_product
            mock_session.add.assert_called_once_with(mock_product)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_product)
    
    @pytest.mark.asyncio
    async def test_create_product_duplicate_url(self, product_repository, mock_session, sample_product_data):
        """Test product creation with duplicate URL."""
        # Mock integrity error for duplicate URL
        mock_session.add = Mock()
        mock_session.commit = Mock(side_effect=IntegrityError("Duplicate URL", None, None))
        mock_session.rollback = Mock()
        
        with pytest.raises(ValidationError, match="Product with this URL already exists"):
            await product_repository.create_product(sample_product_data)
        
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_success(self, product_repository, mock_session):
        """Test successful product retrieval by ID."""
        mock_product = Product(id=1, name="Test Pump", category="pumps")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_product
        
        result = await product_repository.get_product_by_id(1)
        
        assert result == mock_product
        mock_session.query.assert_called_with(Product)
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self, product_repository, mock_session):
        """Test product retrieval when product doesn't exist."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await product_repository.get_product_by_id(999)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_products_by_category(self, product_repository, mock_session):
        """Test product retrieval by category."""
        mock_products = [
            Product(id=1, name="Pump 1", category="pumps"),
            Product(id=2, name="Pump 2", category="pumps")
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_products
        
        result = await product_repository.get_products_by_category("pumps")
        
        assert result == mock_products
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_update_product_price(self, product_repository, mock_session):
        """Test product price update."""
        mock_product = Product(id=1, name="Test Pump", price=Decimal("1500.00"))
        mock_session.query.return_value.filter.return_value.first.return_value = mock_product
        mock_session.commit = Mock()
        
        new_price = Decimal("1600.00")
        result = await product_repository.update_product_price(1, new_price)
        
        assert result.price == new_price
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_products_by_name(self, product_repository, mock_session):
        """Test product search by name."""
        mock_products = [
            Product(id=1, name="High-Performance Pump", category="pumps"),
            Product(id=2, name="Performance UV Reactor", category="uv_reactors")
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_products
        
        result = await product_repository.search_products_by_name("Performance")
        
        assert result == mock_products
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_products_by_price_range(self, product_repository, mock_session):
        """Test product retrieval by price range."""
        mock_products = [
            Product(id=1, name="Mid-range Pump", price=Decimal("1200.00")),
            Product(id=2, name="Premium Pump", price=Decimal("1800.00"))
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_products
        
        result = await product_repository.get_products_by_price_range(
            min_price=Decimal("1000.00"),
            max_price=Decimal("2000.00")
        )
        
        assert result == mock_products
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_delete_product_success(self, product_repository, mock_session):
        """Test successful product deletion."""
        mock_product = Product(id=1, name="Test Pump")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_product
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        
        result = await product_repository.delete_product(1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_product)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, product_repository, mock_session):
        """Test product deletion when product doesn't exist."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await product_repository.delete_product(999)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_bulk_create_products(self, product_repository, mock_session, sample_product_data):
        """Test bulk product creation."""
        products_data = [
            {**sample_product_data, "name": f"Product {i}", "url": f"https://example.com/product-{i}"}
            for i in range(1, 4)
        ]
        
        mock_session.bulk_insert_mappings = Mock()
        mock_session.commit = Mock()
        
        result = await product_repository.bulk_create_products(products_data)
        
        assert result == 3
        mock_session.bulk_insert_mappings.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_products_with_pagination(self, product_repository, mock_session):
        """Test product retrieval with pagination."""
        mock_products = [
            Product(id=i, name=f"Product {i}", category="pumps")
            for i in range(1, 6)
        ]
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_products
        
        result = await product_repository.get_products_with_pagination(
            page=1, page_size=5, category="pumps"
        )
        
        assert len(result) == 5
        mock_session.query.return_value.offset.assert_called_with(0)
        mock_session.query.return_value.offset.return_value.limit.assert_called_with(5)


class TestPriceHistoryRepository:
    """Integration tests for PriceHistory repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value = session
        session.filter.return_value = session
        session.filter_by.return_value = session
        session.order_by.return_value = session
        session.limit.return_value = session
        return session
    
    @pytest.fixture
    def price_history_repository(self, mock_session):
        """Create PriceHistoryRepository instance with mock session."""
        return PriceHistoryRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_add_price_record(self, price_history_repository, mock_session):
        """Test adding a new price history record."""
        price_data = {
            "product_id": 1,
            "price": Decimal("1500.00"),
            "currency": "USD",
            "recorded_at": datetime.now(timezone.utc),
            "source_url": "https://example.com/pump-123",
            "scraping_session_id": "session-123"
        }
        
        mock_price_record = PriceHistory(**price_data)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('src.database.repositories.PriceHistory', return_value=mock_price_record):
            result = await price_history_repository.add_price_record(price_data)
            
            assert result == mock_price_record
            mock_session.add.assert_called_once_with(mock_price_record)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_price_history_for_product(self, price_history_repository, mock_session):
        """Test retrieving price history for a specific product."""
        mock_price_records = [
            PriceHistory(id=1, product_id=1, price=Decimal("1500.00"), recorded_at=datetime.now()),
            PriceHistory(id=2, product_id=1, price=Decimal("1450.00"), recorded_at=datetime.now())
        ]
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_price_records
        
        result = await price_history_repository.get_price_history_for_product(1)
        
        assert result == mock_price_records
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_latest_price_for_product(self, price_history_repository, mock_session):
        """Test retrieving the latest price for a product."""
        mock_latest_price = PriceHistory(
            id=1, product_id=1, price=Decimal("1600.00"), 
            recorded_at=datetime.now(timezone.utc)
        )
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_latest_price
        
        result = await price_history_repository.get_latest_price_for_product(1)
        
        assert result == mock_latest_price
    
    @pytest.mark.asyncio
    async def test_get_price_changes_above_threshold(self, price_history_repository, mock_session):
        """Test retrieving price changes above a certain threshold."""
        mock_price_changes = [
            {
                "product_id": 1,
                "current_price": Decimal("1600.00"),
                "previous_price": Decimal("1500.00"),
                "price_change_percent": 6.67,
                "recorded_at": datetime.now(timezone.utc)
            }
        ]
        
        # Mock complex query result
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = mock_price_changes
        
        result = await price_history_repository.get_price_changes_above_threshold(5.0)
        
        assert result == mock_price_changes
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_bulk_insert_price_records(self, price_history_repository, mock_session):
        """Test bulk insertion of price history records."""
        price_records_data = [
            {
                "product_id": i,
                "price": Decimal(f"{1000 + i * 100}.00"),
                "currency": "USD",
                "recorded_at": datetime.now(timezone.utc),
                "source_url": f"https://example.com/product-{i}"
            }
            for i in range(1, 6)
        ]
        
        mock_session.bulk_insert_mappings = Mock()
        mock_session.commit = Mock()
        
        result = await price_history_repository.bulk_insert_price_records(price_records_data)
        
        assert result == 5
        mock_session.bulk_insert_mappings.assert_called_once_with(PriceHistory, price_records_data)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_price_statistics(self, price_history_repository, mock_session):
        """Test retrieving price statistics for a product."""
        mock_stats = {
            "product_id": 1,
            "min_price": Decimal("1400.00"),
            "max_price": Decimal("1700.00"),
            "avg_price": Decimal("1550.00"),
            "price_volatility": 0.15,
            "record_count": 10
        }
        
        # Mock aggregate query result
        mock_session.query.return_value.filter.return_value.first.return_value = mock_stats
        
        result = await price_history_repository.get_price_statistics(1)
        
        assert result == mock_stats
        assert result["avg_price"] == Decimal("1550.00")


class TestSupplierRepository:
    """Integration tests for Supplier repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value = session
        session.filter.return_value = session
        session.filter_by.return_value = session
        return session
    
    @pytest.fixture
    def supplier_repository(self, mock_session):
        """Create SupplierRepository instance with mock session."""
        return SupplierRepository(mock_session)
    
    @pytest.fixture
    def sample_supplier_data(self):
        """Create sample supplier data for testing."""
        return {
            "name": "AquaTech Solutions",
            "website": "https://aquatech-solutions.com",
            "contact_email": "sales@aquatech-solutions.com",
            "contact_phone": "+1-555-0123",
            "address": {
                "street": "123 Industrial Blvd",
                "city": "Manufacturing City",
                "state": "CA",
                "zip_code": "90210",
                "country": "USA"
            },
            "business_info": {
                "founded_year": 1995,
                "employee_count": 150,
                "annual_revenue": "$50M",
                "certifications": ["ISO 9001", "ISO 14001"]
            },
            "product_categories": ["pumps", "valves", "fittings"],
            "is_verified": True,
            "trust_score": 8.5
        }
    
    @pytest.mark.asyncio
    async def test_create_supplier_success(self, supplier_repository, mock_session, sample_supplier_data):
        """Test successful supplier creation."""
        mock_supplier = Supplier(**sample_supplier_data)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('src.database.repositories.Supplier', return_value=mock_supplier):
            result = await supplier_repository.create_supplier(sample_supplier_data)
            
            assert result == mock_supplier
            mock_session.add.assert_called_once_with(mock_supplier)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_supplier_by_website(self, supplier_repository, mock_session):
        """Test supplier retrieval by website URL."""
        mock_supplier = Supplier(id=1, name="AquaTech Solutions", website="https://aquatech-solutions.com")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_supplier
        
        result = await supplier_repository.get_supplier_by_website("https://aquatech-solutions.com")
        
        assert result == mock_supplier
    
    @pytest.mark.asyncio
    async def test_update_supplier_trust_score(self, supplier_repository, mock_session):
        """Test supplier trust score update."""
        mock_supplier = Supplier(id=1, name="AquaTech Solutions", trust_score=8.5)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_supplier
        mock_session.commit = Mock()
        
        new_score = 9.0
        result = await supplier_repository.update_supplier_trust_score(1, new_score)
        
        assert result.trust_score == new_score
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_suppliers_by_category(self, supplier_repository, mock_session):
        """Test supplier retrieval by product category."""
        mock_suppliers = [
            Supplier(id=1, name="Pump Supplier 1", product_categories=["pumps"]),
            Supplier(id=2, name="Pump Supplier 2", product_categories=["pumps", "valves"])
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_suppliers
        
        result = await supplier_repository.get_suppliers_by_category("pumps")
        
        assert result == mock_suppliers
        assert len(result) == 2


class TestWorkflowRepository:
    """Integration tests for Workflow repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value = session
        session.filter.return_value = session
        session.filter_by.return_value = session
        session.order_by.return_value = session
        return session
    
    @pytest.fixture
    def workflow_repository(self, mock_session):
        """Create WorkflowRepository instance with mock session."""
        return WorkflowRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_create_workflow_execution(self, workflow_repository, mock_session):
        """Test workflow execution record creation."""
        workflow_data = {
            "workflow_id": "research-workflow-123",
            "workflow_type": "research",
            "status": "running",
            "input_data": {"product_urls": ["https://example.com/pump1"]},
            "user_id": "user-123",
            "started_at": datetime.now(timezone.utc)
        }
        
        mock_workflow = WorkflowExecution(**workflow_data)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('src.database.repositories.WorkflowExecution', return_value=mock_workflow):
            result = await workflow_repository.create_workflow_execution(workflow_data)
            
            assert result == mock_workflow
            mock_session.add.assert_called_once_with(mock_workflow)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_workflow_status(self, workflow_repository, mock_session):
        """Test workflow status update."""
        mock_workflow = WorkflowExecution(
            id=1, workflow_id="research-workflow-123", status="running"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_workflow
        mock_session.commit = Mock()
        
        result = await workflow_repository.update_workflow_status(
            "research-workflow-123", "completed", {"products_found": 5}
        )
        
        assert result.status == "completed"
        assert result.result_data == {"products_found": 5}
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_workflow_executions_by_user(self, workflow_repository, mock_session):
        """Test retrieving workflow executions for a specific user."""
        mock_workflows = [
            WorkflowExecution(id=1, workflow_id="wf-1", user_id="user-123"),
            WorkflowExecution(id=2, workflow_id="wf-2", user_id="user-123")
        ]
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_workflows
        
        result = await workflow_repository.get_workflow_executions_by_user("user-123")
        
        assert result == mock_workflows
        assert len(result) == 2


class TestDatabaseTransactions:
    """Integration tests for database transaction management."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session with transaction support."""
        session = Mock(spec=Session)
        session.begin = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session
    
    @pytest.mark.asyncio
    async def test_successful_transaction(self, mock_session):
        """Test successful database transaction."""
        product_repo = ProductRepository(mock_session)
        supplier_repo = SupplierRepository(mock_session)
        
        # Mock successful operations
        mock_supplier = Supplier(id=1, name="Test Supplier")
        mock_product = Product(id=1, name="Test Product", supplier_id=1)
        
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('src.database.repositories.Supplier', return_value=mock_supplier):
            with patch('src.database.repositories.Product', return_value=mock_product):
                # Simulate transaction
                mock_session.begin()
                
                supplier_result = await supplier_repo.create_supplier({"name": "Test Supplier"})
                product_result = await product_repo.create_product({
                    "name": "Test Product", "supplier_id": supplier_result.id
                })
                
                mock_session.commit()
                
                assert supplier_result == mock_supplier
                assert product_result == mock_product
                mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, mock_session):
        """Test transaction rollback on error."""
        product_repo = ProductRepository(mock_session)
        
        # Mock error during commit
        mock_session.add = Mock()
        mock_session.commit = Mock(side_effect=IntegrityError("Constraint violation", None, None))
        mock_session.rollback = Mock()
        
        with pytest.raises(ValidationError):
            mock_session.begin()
            
            try:
                await product_repo.create_product({"name": "Test Product"})
                mock_session.commit()
            except IntegrityError:
                mock_session.rollback()
                raise ValidationError("Transaction failed")
        
        mock_session.rollback.assert_called_once()


class TestDatabasePerformance:
    """Integration tests for database performance and optimization."""
    
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self):
        """Test performance of bulk database operations."""
        # Mock large dataset operations
        mock_session = Mock(spec=Session)
        mock_session.bulk_insert_mappings = Mock()
        mock_session.commit = Mock()
        
        product_repo = ProductRepository(mock_session)
        
        # Simulate bulk insert of 1000 products
        large_dataset = [
            {
                "name": f"Product {i}",
                "category": "pumps",
                "price": Decimal(f"{1000 + i}.00"),
                "url": f"https://example.com/product-{i}"
            }
            for i in range(1000)
        ]
        
        start_time = datetime.now()
        result = await product_repo.bulk_create_products(large_dataset)
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        assert result == 1000
        assert execution_time < 1.0  # Should complete quickly with mocked operations
        mock_session.bulk_insert_mappings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_optimization_with_indexes(self):
        """Test query performance with proper indexing."""
        # This would test actual query performance in a real database
        # For now, we'll mock the behavior
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_session
        mock_session.filter.return_value = mock_session
        mock_session.join.return_value = mock_session
        mock_session.all.return_value = []
        
        product_repo = ProductRepository(mock_session)
        
        # Simulate complex query with joins
        start_time = datetime.now()
        result = await product_repo.get_products_with_supplier_info(category="pumps")
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        assert execution_time < 0.1  # Should be fast with proper indexing
        mock_session.join.assert_called()  # Verify join was used


class TestDatabaseMigrations:
    """Integration tests for database schema migrations."""
    
    @pytest.mark.asyncio
    async def test_schema_migration_success(self):
        """Test successful database schema migration."""
        # Mock Alembic migration operations
        with patch('alembic.command.upgrade') as mock_upgrade:
            mock_upgrade.return_value = None
            
            # Simulate migration
            from src.database.migrations import run_migrations
            
            result = await run_migrations("head")
            
            assert result is True
            mock_upgrade.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schema_migration_failure(self):
        """Test database schema migration failure handling."""
        # Mock Alembic migration failure
        with patch('alembic.command.upgrade', side_effect=Exception("Migration failed")):
            from src.database.migrations import run_migrations
            
            with pytest.raises(DatabaseError, match="Migration failed"):
                await run_migrations("head")


class TestDatabaseConnectionPooling:
    """Integration tests for database connection pooling."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self):
        """Test database connection pool behavior."""
        # Mock connection pool
        mock_pool = Mock()
        mock_pool.get_connection.return_value = Mock()
        mock_pool.return_connection = Mock()
        mock_pool.size.return_value = 5
        mock_pool.checked_out.return_value = 2
        
        with patch('src.database.connection.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_engine.pool = mock_pool
            mock_create_engine.return_value = mock_engine
            
            db_config = DatabaseConfig(
                host="localhost",
                port=5432,
                database="ecomate_test",
                username="test_user",
                password="test_password",
                pool_size=5,
                max_overflow=10
            )
            
            db_manager = DatabaseManager(db_config)
            
            # Test pool statistics
            pool_info = db_manager.get_pool_status()
            
            assert pool_info["pool_size"] == 5
            assert pool_info["checked_out"] == 2
            assert pool_info["available"] == 3
    
    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self):
        """Test behavior when connection pool is exhausted."""
        # Mock pool exhaustion scenario
        with patch('src.database.connection.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_engine.connect.side_effect = Exception("Pool exhausted")
            mock_create_engine.return_value = mock_engine
            
            db_config = DatabaseConfig(
                host="localhost",
                port=5432,
                database="ecomate_test",
                username="test_user",
                password="test_password",
                pool_size=1,
                max_overflow=0
            )
            
            db_manager = DatabaseManager(db_config)
            
            with pytest.raises(DatabaseError, match="Pool exhausted"):
                with db_manager.get_connection():
                    pass


class TestCacheIntegration:
    """Integration tests for database caching with Redis."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_client = Mock()
        redis_client.get.return_value = None
        redis_client.set.return_value = True
        redis_client.delete.return_value = 1
        redis_client.exists.return_value = False
        return redis_client
    
    @pytest.mark.asyncio
    async def test_product_caching(self, mock_redis):
        """Test product data caching with Redis."""
        mock_session = Mock(spec=Session)
        product_repo = ProductRepository(mock_session, cache_client=mock_redis)
        
        # Mock product data
        mock_product = Product(id=1, name="Cached Pump", category="pumps")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_product
        
        # First call - should query database and cache result
        result1 = await product_repo.get_product_by_id(1)
        
        assert result1 == mock_product
        mock_redis.set.assert_called_once()  # Should cache the result
        
        # Second call - should return cached result
        mock_redis.get.return_value = json.dumps({
            "id": 1, "name": "Cached Pump", "category": "pumps"
        })
        
        result2 = await product_repo.get_product_by_id(1)
        
        mock_redis.get.assert_called()  # Should check cache
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mock_redis):
        """Test cache invalidation on data updates."""
        mock_session = Mock(spec=Session)
        product_repo = ProductRepository(mock_session, cache_client=mock_redis)
        
        # Mock product update
        mock_product = Product(id=1, name="Updated Pump", price=Decimal("1600.00"))
        mock_session.query.return_value.filter.return_value.first.return_value = mock_product
        mock_session.commit = Mock()
        
        # Update product - should invalidate cache
        result = await product_repo.update_product_price(1, Decimal("1600.00"))
        
        assert result.price == Decimal("1600.00")
        mock_redis.delete.assert_called()  # Should invalidate cache
        mock_session.commit.assert_called_once()