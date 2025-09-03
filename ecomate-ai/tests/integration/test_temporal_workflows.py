"""Integration tests for Temporal workflows and activities."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import json
from temporalio import workflow, activity
from temporalio.client import Client, WorkflowHandle
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from temporalio.common import RetryPolicy

from src.workflows.research_workflow import (
    ResearchWorkflow,
    ResearchWorkflowInput,
    ResearchWorkflowResult,
    ProductResearchActivity,
    DataValidationActivity,
    StorageActivity
)
from src.workflows.price_monitoring_workflow import (
    PriceMonitoringWorkflow,
    PriceMonitoringInput,
    PriceMonitoringResult,
    PriceCheckActivity,
    NotificationActivity,
    HistoryUpdateActivity
)
from src.workflows.data_processing_workflow import (
    DataProcessingWorkflow,
    DataProcessingInput,
    DataProcessingResult,
    DataCleaningActivity,
    DataEnrichmentActivity,
    DataPersistenceActivity
)
from src.models.product import ProductBase, PumpSpecification, UVReactorSpecification
from src.models.supplier import Supplier
from src.models.scraping import ScrapingResult
from src.utils.exceptions import WorkflowError, ActivityError, ValidationError


class TestResearchWorkflow:
    """Integration tests for research workflow."""
    
    @pytest.fixture
    async def workflow_environment(self):
        """Create a Temporal workflow testing environment."""
        async with WorkflowEnvironment() as env:
            yield env
    
    @pytest.fixture
    def research_input(self):
        """Create research workflow input for testing."""
        return ResearchWorkflowInput(
            product_urls=[
                "https://example.com/pump1",
                "https://example.com/pump2",
                "https://example.com/uv-reactor1"
            ],
            research_type="comprehensive",
            priority="high",
            user_id="test-user-123",
            request_id="req-456",
            filters={
                "min_price": 100,
                "max_price": 5000,
                "categories": ["pumps", "uv_reactors"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_research_workflow_success(self, workflow_environment, research_input):
        """Test successful research workflow execution."""
        # Mock activities
        async def mock_product_research(urls: List[str]) -> List[Dict[str, Any]]:
            return [
                {
                    "url": "https://example.com/pump1",
                    "name": "High-Performance Pump",
                    "price": 1500.00,
                    "specifications": {
                        "flow_rate": 100,
                        "head_pressure": 50,
                        "power_consumption": 750
                    },
                    "supplier": "AquaTech Solutions",
                    "category": "pumps"
                },
                {
                    "url": "https://example.com/uv-reactor1",
                    "name": "UV Sterilizer Pro",
                    "price": 2200.00,
                    "specifications": {
                        "uv_dose": 40,
                        "flow_rate": 80,
                        "lamp_power": 120
                    },
                    "supplier": "UV Systems Inc",
                    "category": "uv_reactors"
                }
            ]
        
        async def mock_data_validation(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            # Simulate validation and return validated products
            validated = []
            for product in products:
                if product.get("price", 0) > 0 and product.get("name"):
                    validated.append({
                        **product,
                        "validated": True,
                        "validation_score": 0.95
                    })
            return validated
        
        async def mock_storage(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {
                "stored_count": len(products),
                "storage_location": "s3://ecomate-data/research/req-456/",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="research-queue",
            workflows=[ResearchWorkflow],
            activities=[
                mock_product_research,
                mock_data_validation,
                mock_storage
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                ResearchWorkflow.run,
                research_input,
                id=f"research-{research_input.request_id}",
                task_queue="research-queue",
                execution_timeout=timedelta(minutes=10)
            )
            
            assert isinstance(result, ResearchWorkflowResult)
            assert result.success is True
            assert result.products_found == 2
            assert result.products_validated == 2
            assert result.request_id == "req-456"
            assert len(result.products) == 2
    
    @pytest.mark.asyncio
    async def test_research_workflow_with_failures(self, workflow_environment, research_input):
        """Test research workflow handling activity failures."""
        # Mock activities with some failures
        async def mock_product_research_with_failures(urls: List[str]) -> List[Dict[str, Any]]:
            # Simulate partial failures
            results = []
            for i, url in enumerate(urls):
                if i == 1:  # Second URL fails
                    continue
                results.append({
                    "url": url,
                    "name": f"Product {i}",
                    "price": 1000 + i * 500,
                    "specifications": {"test": True},
                    "supplier": "Test Supplier",
                    "category": "pumps"
                })
            return results
        
        async def mock_data_validation_with_errors(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            # Simulate validation that filters out some products
            validated = []
            for product in products:
                if product.get("price", 0) > 1200:  # Only expensive products pass
                    validated.append({
                        **product,
                        "validated": True,
                        "validation_score": 0.85
                    })
            return validated
        
        async def mock_storage_success(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {
                "stored_count": len(products),
                "storage_location": "s3://ecomate-data/research/req-456/",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="research-queue",
            workflows=[ResearchWorkflow],
            activities=[
                mock_product_research_with_failures,
                mock_data_validation_with_errors,
                mock_storage_success
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                ResearchWorkflow.run,
                research_input,
                id=f"research-failures-{research_input.request_id}",
                task_queue="research-queue",
                execution_timeout=timedelta(minutes=10)
            )
            
            assert isinstance(result, ResearchWorkflowResult)
            assert result.success is True  # Workflow succeeds even with partial failures
            assert result.products_found == 2  # Only 2 URLs processed successfully
            assert result.products_validated == 1  # Only 1 product passed validation
            assert len(result.products) == 1
    
    @pytest.mark.asyncio
    async def test_research_workflow_timeout(self, workflow_environment, research_input):
        """Test research workflow timeout handling."""
        # Mock slow activity
        async def mock_slow_product_research(urls: List[str]) -> List[Dict[str, Any]]:
            await asyncio.sleep(15)  # Longer than workflow timeout
            return []
        
        async def mock_data_validation(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return products
        
        async def mock_storage(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"stored_count": 0}
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="research-queue",
            workflows=[ResearchWorkflow],
            activities=[
                mock_slow_product_research,
                mock_data_validation,
                mock_storage
            ]
        ):
            # Execute workflow with short timeout
            with pytest.raises(Exception):  # Should timeout
                await workflow_environment.client.execute_workflow(
                    ResearchWorkflow.run,
                    research_input,
                    id=f"research-timeout-{research_input.request_id}",
                    task_queue="research-queue",
                    execution_timeout=timedelta(seconds=5)
                )
    
    @pytest.mark.asyncio
    async def test_research_workflow_retry_logic(self, workflow_environment, research_input):
        """Test research workflow retry logic for failed activities."""
        call_count = 0
        
        async def mock_flaky_product_research(urls: List[str]) -> List[Dict[str, Any]]:
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:  # Fail first 2 attempts
                raise ActivityError("Temporary network error")
            
            # Succeed on 3rd attempt
            return [{
                "url": urls[0],
                "name": "Retry Success Product",
                "price": 1000,
                "specifications": {},
                "supplier": "Reliable Supplier",
                "category": "pumps"
            }]
        
        async def mock_data_validation(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [{
                **product,
                "validated": True,
                "validation_score": 0.9
            } for product in products]
        
        async def mock_storage(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"stored_count": len(products)}
        
        # Register activities with retry policy
        async with Worker(
            workflow_environment.client,
            task_queue="research-queue",
            workflows=[ResearchWorkflow],
            activities=[
                mock_flaky_product_research,
                mock_data_validation,
                mock_storage
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                ResearchWorkflow.run,
                research_input,
                id=f"research-retry-{research_input.request_id}",
                task_queue="research-queue",
                execution_timeout=timedelta(minutes=5)
            )
            
            assert result.success is True
            assert call_count == 3  # Should have retried 3 times
            assert result.products_found == 1


class TestPriceMonitoringWorkflow:
    """Integration tests for price monitoring workflow."""
    
    @pytest.fixture
    def monitoring_input(self):
        """Create price monitoring workflow input for testing."""
        return PriceMonitoringInput(
            product_ids=["prod-123", "prod-456", "prod-789"],
            monitoring_frequency="daily",
            price_change_threshold=0.05,  # 5% change threshold
            notification_settings={
                "email": True,
                "webhook": True,
                "recipients": ["admin@ecomate.com"]
            },
            user_id="monitor-user-123"
        )
    
    @pytest.mark.asyncio
    async def test_price_monitoring_workflow_success(self, workflow_environment, monitoring_input):
        """Test successful price monitoring workflow execution."""
        # Mock activities
        async def mock_price_check(product_ids: List[str]) -> List[Dict[str, Any]]:
            return [
                {
                    "product_id": "prod-123",
                    "current_price": 1450.00,
                    "previous_price": 1500.00,
                    "price_change": -0.033,  # 3.3% decrease
                    "url": "https://example.com/pump1",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                {
                    "product_id": "prod-456",
                    "current_price": 2350.00,
                    "previous_price": 2200.00,
                    "price_change": 0.068,  # 6.8% increase (above threshold)
                    "url": "https://example.com/uv-reactor1",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                {
                    "product_id": "prod-789",
                    "current_price": 800.00,
                    "previous_price": 800.00,
                    "price_change": 0.0,  # No change
                    "url": "https://example.com/filter1",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        
        async def mock_notification(price_changes: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
            # Only notify for significant changes
            significant_changes = [
                change for change in price_changes 
                if abs(change["price_change"]) >= 0.05
            ]
            
            return {
                "notifications_sent": len(significant_changes),
                "recipients_notified": len(settings.get("recipients", [])),
                "notification_methods": ["email", "webhook"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        async def mock_history_update(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {
                "records_updated": len(price_data),
                "database_location": "postgresql://ecomate-db/price_history",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="monitoring-queue",
            workflows=[PriceMonitoringWorkflow],
            activities=[
                mock_price_check,
                mock_notification,
                mock_history_update
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                PriceMonitoringWorkflow.run,
                monitoring_input,
                id=f"monitoring-{monitoring_input.user_id}",
                task_queue="monitoring-queue",
                execution_timeout=timedelta(minutes=10)
            )
            
            assert isinstance(result, PriceMonitoringResult)
            assert result.success is True
            assert result.products_checked == 3
            assert result.price_changes_detected == 1  # Only prod-456 above threshold
            assert result.notifications_sent == 1
    
    @pytest.mark.asyncio
    async def test_price_monitoring_workflow_no_changes(self, workflow_environment, monitoring_input):
        """Test price monitoring workflow when no significant price changes occur."""
        # Mock activities with no significant changes
        async def mock_price_check_no_changes(product_ids: List[str]) -> List[Dict[str, Any]]:
            return [
                {
                    "product_id": product_id,
                    "current_price": 1000.00,
                    "previous_price": 1000.00,
                    "price_change": 0.0,
                    "url": f"https://example.com/{product_id}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                for product_id in product_ids
            ]
        
        async def mock_notification_none(price_changes: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "notifications_sent": 0,
                "recipients_notified": 0,
                "notification_methods": [],
                "reason": "No significant price changes detected"
            }
        
        async def mock_history_update(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"records_updated": len(price_data)}
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="monitoring-queue",
            workflows=[PriceMonitoringWorkflow],
            activities=[
                mock_price_check_no_changes,
                mock_notification_none,
                mock_history_update
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                PriceMonitoringWorkflow.run,
                monitoring_input,
                id=f"monitoring-no-changes-{monitoring_input.user_id}",
                task_queue="monitoring-queue",
                execution_timeout=timedelta(minutes=10)
            )
            
            assert result.success is True
            assert result.products_checked == 3
            assert result.price_changes_detected == 0
            assert result.notifications_sent == 0
    
    @pytest.mark.asyncio
    async def test_price_monitoring_workflow_partial_failures(self, workflow_environment, monitoring_input):
        """Test price monitoring workflow with some product check failures."""
        # Mock activities with partial failures
        async def mock_price_check_partial_failure(product_ids: List[str]) -> List[Dict[str, Any]]:
            results = []
            for i, product_id in enumerate(product_ids):
                if i == 1:  # Second product fails to check
                    continue
                
                results.append({
                    "product_id": product_id,
                    "current_price": 1000 + i * 100,
                    "previous_price": 1000,
                    "price_change": i * 0.1,
                    "url": f"https://example.com/{product_id}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return results
        
        async def mock_notification(price_changes: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
            significant_changes = [
                change for change in price_changes 
                if abs(change["price_change"]) >= 0.05
            ]
            return {"notifications_sent": len(significant_changes)}
        
        async def mock_history_update(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"records_updated": len(price_data)}
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="monitoring-queue",
            workflows=[PriceMonitoringWorkflow],
            activities=[
                mock_price_check_partial_failure,
                mock_notification,
                mock_history_update
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                PriceMonitoringWorkflow.run,
                monitoring_input,
                id=f"monitoring-partial-{monitoring_input.user_id}",
                task_queue="monitoring-queue",
                execution_timeout=timedelta(minutes=10)
            )
            
            assert result.success is True
            assert result.products_checked == 2  # Only 2 products checked successfully
            assert result.failed_checks == 1  # 1 product failed


class TestDataProcessingWorkflow:
    """Integration tests for data processing workflow."""
    
    @pytest.fixture
    def processing_input(self):
        """Create data processing workflow input for testing."""
        return DataProcessingInput(
            data_source="s3://ecomate-raw/batch-2024-01-15/",
            processing_type="batch",
            output_destination="s3://ecomate-processed/batch-2024-01-15/",
            processing_rules={
                "remove_duplicates": True,
                "validate_prices": True,
                "enrich_supplier_data": True,
                "normalize_specifications": True
            },
            batch_id="batch-2024-01-15-001",
            user_id="processor-user-123"
        )
    
    @pytest.mark.asyncio
    async def test_data_processing_workflow_success(self, workflow_environment, processing_input):
        """Test successful data processing workflow execution."""
        # Mock activities
        async def mock_data_cleaning(source: str, rules: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "records_processed": 1000,
                "duplicates_removed": 50,
                "invalid_records_filtered": 25,
                "cleaning_rules_applied": list(rules.keys()),
                "output_location": "temp://cleaned-data/"
            }
        
        async def mock_data_enrichment(cleaned_data_location: str) -> Dict[str, Any]:
            return {
                "records_enriched": 925,  # 1000 - 50 - 25
                "supplier_data_added": 800,
                "specifications_normalized": 900,
                "enrichment_sources": ["supplier_api", "product_catalog"],
                "output_location": "temp://enriched-data/"
            }
        
        async def mock_data_persistence(enriched_data_location: str, destination: str) -> Dict[str, Any]:
            return {
                "records_stored": 925,
                "storage_location": destination,
                "storage_format": "parquet",
                "compression": "snappy",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="processing-queue",
            workflows=[DataProcessingWorkflow],
            activities=[
                mock_data_cleaning,
                mock_data_enrichment,
                mock_data_persistence
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                DataProcessingWorkflow.run,
                processing_input,
                id=f"processing-{processing_input.batch_id}",
                task_queue="processing-queue",
                execution_timeout=timedelta(minutes=30)
            )
            
            assert isinstance(result, DataProcessingResult)
            assert result.success is True
            assert result.records_processed == 1000
            assert result.records_cleaned == 925
            assert result.records_enriched == 925
            assert result.records_stored == 925
            assert result.batch_id == "batch-2024-01-15-001"
    
    @pytest.mark.asyncio
    async def test_data_processing_workflow_with_errors(self, workflow_environment, processing_input):
        """Test data processing workflow with processing errors."""
        # Mock activities with errors
        async def mock_data_cleaning_with_errors(source: str, rules: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "records_processed": 1000,
                "duplicates_removed": 50,
                "invalid_records_filtered": 200,  # More invalid records
                "processing_errors": 10,
                "cleaning_rules_applied": list(rules.keys()),
                "output_location": "temp://cleaned-data/"
            }
        
        async def mock_data_enrichment_partial(cleaned_data_location: str) -> Dict[str, Any]:
            return {
                "records_enriched": 600,  # Some enrichment failures
                "enrichment_failures": 140,
                "supplier_data_added": 500,
                "specifications_normalized": 580,
                "enrichment_sources": ["supplier_api"],  # One source failed
                "output_location": "temp://enriched-data/"
            }
        
        async def mock_data_persistence_success(enriched_data_location: str, destination: str) -> Dict[str, Any]:
            return {
                "records_stored": 600,
                "storage_location": destination,
                "storage_format": "parquet",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="processing-queue",
            workflows=[DataProcessingWorkflow],
            activities=[
                mock_data_cleaning_with_errors,
                mock_data_enrichment_partial,
                mock_data_persistence_success
            ]
        ):
            # Execute workflow
            result = await workflow_environment.client.execute_workflow(
                DataProcessingWorkflow.run,
                processing_input,
                id=f"processing-errors-{processing_input.batch_id}",
                task_queue="processing-queue",
                execution_timeout=timedelta(minutes=30)
            )
            
            assert result.success is True  # Workflow succeeds despite errors
            assert result.records_processed == 1000
            assert result.records_stored == 600  # Fewer records due to errors
            assert result.processing_errors > 0


class TestWorkflowInteractions:
    """Integration tests for workflow interactions and dependencies."""
    
    @pytest.mark.asyncio
    async def test_research_to_monitoring_workflow_chain(self, workflow_environment):
        """Test chaining research workflow output to price monitoring workflow."""
        # First, run research workflow
        research_input = ResearchWorkflowInput(
            product_urls=["https://example.com/pump1"],
            research_type="basic",
            priority="medium",
            user_id="chain-test-user",
            request_id="chain-req-123"
        )
        
        # Mock research activities
        async def mock_research_activity(urls: List[str]) -> List[Dict[str, Any]]:
            return [{
                "url": urls[0],
                "product_id": "discovered-prod-123",
                "name": "Discovered Pump",
                "price": 1200.00,
                "specifications": {},
                "supplier": "Test Supplier",
                "category": "pumps"
            }]
        
        async def mock_validation(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [{**p, "validated": True} for p in products]
        
        async def mock_storage(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"stored_count": len(products)}
        
        # Mock monitoring activities
        async def mock_price_check_chain(product_ids: List[str]) -> List[Dict[str, Any]]:
            return [{
                "product_id": product_ids[0],
                "current_price": 1150.00,  # Price decreased
                "previous_price": 1200.00,
                "price_change": -0.042,
                "url": "https://example.com/pump1",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        
        async def mock_notification_chain(price_changes: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
            return {"notifications_sent": 0}  # Below threshold
        
        async def mock_history_update_chain(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"records_updated": len(price_data)}
        
        # Register all activities
        async with Worker(
            workflow_environment.client,
            task_queue="chain-queue",
            workflows=[ResearchWorkflow, PriceMonitoringWorkflow],
            activities=[
                mock_research_activity,
                mock_validation,
                mock_storage,
                mock_price_check_chain,
                mock_notification_chain,
                mock_history_update_chain
            ]
        ):
            # Execute research workflow
            research_result = await workflow_environment.client.execute_workflow(
                ResearchWorkflow.run,
                research_input,
                id="chain-research",
                task_queue="chain-queue",
                execution_timeout=timedelta(minutes=5)
            )
            
            assert research_result.success is True
            assert len(research_result.products) == 1
            
            # Extract product ID for monitoring
            discovered_product_id = research_result.products[0].get("product_id")
            
            # Create monitoring input using discovered product
            monitoring_input = PriceMonitoringInput(
                product_ids=[discovered_product_id],
                monitoring_frequency="daily",
                price_change_threshold=0.05,
                notification_settings={"email": True, "recipients": ["test@example.com"]},
                user_id="chain-test-user"
            )
            
            # Execute monitoring workflow
            monitoring_result = await workflow_environment.client.execute_workflow(
                PriceMonitoringWorkflow.run,
                monitoring_input,
                id="chain-monitoring",
                task_queue="chain-queue",
                execution_timeout=timedelta(minutes=5)
            )
            
            assert monitoring_result.success is True
            assert monitoring_result.products_checked == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, workflow_environment):
        """Test concurrent execution of multiple workflows."""
        # Create multiple workflow inputs
        research_inputs = [
            ResearchWorkflowInput(
                product_urls=[f"https://example.com/product{i}"],
                research_type="basic",
                priority="medium",
                user_id=f"concurrent-user-{i}",
                request_id=f"concurrent-req-{i}"
            )
            for i in range(3)
        ]
        
        # Mock activities
        async def mock_concurrent_research(urls: List[str]) -> List[Dict[str, Any]]:
            # Simulate different processing times
            await asyncio.sleep(0.1)
            return [{
                "url": urls[0],
                "name": f"Product from {urls[0]}",
                "price": 1000,
                "specifications": {},
                "supplier": "Concurrent Supplier",
                "category": "pumps"
            }]
        
        async def mock_concurrent_validation(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [{**p, "validated": True} for p in products]
        
        async def mock_concurrent_storage(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"stored_count": len(products)}
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="concurrent-queue",
            workflows=[ResearchWorkflow],
            activities=[
                mock_concurrent_research,
                mock_concurrent_validation,
                mock_concurrent_storage
            ]
        ):
            # Execute workflows concurrently
            tasks = [
                workflow_environment.client.execute_workflow(
                    ResearchWorkflow.run,
                    research_input,
                    id=f"concurrent-{research_input.request_id}",
                    task_queue="concurrent-queue",
                    execution_timeout=timedelta(minutes=5)
                )
                for research_input in research_inputs
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(result.success for result in results)
            assert all(len(result.products) == 1 for result in results)


class TestWorkflowErrorHandling:
    """Integration tests for workflow error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_workflow_activity_retry_exhaustion(self, workflow_environment):
        """Test workflow behavior when activity retries are exhausted."""
        research_input = ResearchWorkflowInput(
            product_urls=["https://example.com/failing-product"],
            research_type="basic",
            priority="high",
            user_id="retry-test-user",
            request_id="retry-req-123"
        )
        
        # Mock activity that always fails
        async def mock_always_failing_research(urls: List[str]) -> List[Dict[str, Any]]:
            raise ActivityError("Persistent failure - service unavailable")
        
        async def mock_validation(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return products
        
        async def mock_storage(products: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {"stored_count": len(products)}
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="retry-queue",
            workflows=[ResearchWorkflow],
            activities=[
                mock_always_failing_research,
                mock_validation,
                mock_storage
            ]
        ):
            # Execute workflow - should handle activity failure gracefully
            result = await workflow_environment.client.execute_workflow(
                ResearchWorkflow.run,
                research_input,
                id="retry-exhaustion-test",
                task_queue="retry-queue",
                execution_timeout=timedelta(minutes=5)
            )
            
            # Workflow should complete but indicate failure
            assert result.success is False
            assert "Persistent failure" in result.error_message
            assert result.products_found == 0
    
    @pytest.mark.asyncio
    async def test_workflow_compensation_logic(self, workflow_environment):
        """Test workflow compensation/rollback logic on failures."""
        # This would test scenarios where workflows need to undo
        # partially completed work when later steps fail
        pass


class TestWorkflowPerformance:
    """Integration tests for workflow performance and scalability."""
    
    @pytest.mark.asyncio
    async def test_large_batch_processing_workflow(self, workflow_environment):
        """Test workflow performance with large data batches."""
        # Create input for large batch processing
        processing_input = DataProcessingInput(
            data_source="s3://ecomate-raw/large-batch/",
            processing_type="batch",
            output_destination="s3://ecomate-processed/large-batch/",
            processing_rules={"remove_duplicates": True, "validate_prices": True},
            batch_id="large-batch-001",
            user_id="performance-test-user"
        )
        
        # Mock activities that simulate large data processing
        async def mock_large_data_cleaning(source: str, rules: Dict[str, Any]) -> Dict[str, Any]:
            # Simulate processing time for large dataset
            await asyncio.sleep(0.5)
            return {
                "records_processed": 100000,
                "duplicates_removed": 5000,
                "invalid_records_filtered": 2000,
                "output_location": "temp://large-cleaned-data/"
            }
        
        async def mock_large_data_enrichment(cleaned_data_location: str) -> Dict[str, Any]:
            await asyncio.sleep(0.3)
            return {
                "records_enriched": 93000,
                "enrichment_failures": 0,
                "output_location": "temp://large-enriched-data/"
            }
        
        async def mock_large_data_persistence(enriched_data_location: str, destination: str) -> Dict[str, Any]:
            await asyncio.sleep(0.2)
            return {
                "records_stored": 93000,
                "storage_location": destination,
                "storage_format": "parquet"
            }
        
        # Register activities
        async with Worker(
            workflow_environment.client,
            task_queue="performance-queue",
            workflows=[DataProcessingWorkflow],
            activities=[
                mock_large_data_cleaning,
                mock_large_data_enrichment,
                mock_large_data_persistence
            ]
        ):
            # Measure execution time
            start_time = datetime.now()
            
            result = await workflow_environment.client.execute_workflow(
                DataProcessingWorkflow.run,
                processing_input,
                id="large-batch-performance",
                task_queue="performance-queue",
                execution_timeout=timedelta(minutes=10)
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            assert result.success is True
            assert result.records_processed == 100000
            assert result.records_stored == 93000
            assert execution_time < 60  # Should complete within 1 minute
    
    @pytest.mark.asyncio
    async def test_workflow_memory_usage(self, workflow_environment):
        """Test workflow memory usage patterns."""
        # This would test memory usage during workflow execution
        # Implementation depends on specific memory monitoring requirements
        pass