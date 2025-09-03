"""Temporal workflow fixtures and mock data for testing."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from temporalio.client import Client, WorkflowHandle
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment


@pytest.fixture
async def temporal_test_environment():
    """Create Temporal test environment for workflow testing."""
    async with WorkflowEnvironment() as env:
        yield env


@pytest.fixture
def mock_temporal_client():
    """Create a mock Temporal client for testing."""
    client = Mock(spec=Client)
    
    # Mock workflow handle
    mock_handle = Mock(spec=WorkflowHandle)
    mock_handle.id = "test-workflow-123"
    mock_handle.result_run_id = "run-456"
    mock_handle.result = AsyncMock(return_value={"status": "completed"})
    mock_handle.query = AsyncMock(return_value={"progress": 50})
    mock_handle.signal = AsyncMock()
    mock_handle.cancel = AsyncMock()
    mock_handle.terminate = AsyncMock()
    
    # Configure client methods
    client.start_workflow = AsyncMock(return_value=mock_handle)
    client.get_workflow_handle = Mock(return_value=mock_handle)
    client.list_workflows = AsyncMock(return_value=[])
    
    return client


@pytest.fixture
def mock_temporal_worker():
    """Create a mock Temporal worker for testing."""
    worker = Mock(spec=Worker)
    worker.run = AsyncMock()
    worker.shutdown = AsyncMock()
    return worker


@pytest.fixture
def sample_workflow_inputs():
    """Create sample workflow input data for testing."""
    return {
        "research_workflow_input": {
            "workflow_id": "research-workflow-123",
            "user_id": "user-123",
            "product_urls": [
                "https://aquatech-solutions.com/centrifugal-pump-cp-100",
                "https://watertech-pro.com/uv-reactor-uv-55r",
                "https://industrial-pumps.com/heavy-duty-pump-hd-500"
            ],
            "categories": ["pumps", "uv_reactors"],
            "research_criteria": {
                "max_price": Decimal("5000.00"),
                "min_flow_rate": 50,
                "required_certifications": ["NSF", "UL"],
                "preferred_materials": ["stainless steel", "duplex stainless steel"],
                "max_lead_time_days": 30
            },
            "priority": "high",
            "deadline": datetime.now(timezone.utc) + timedelta(hours=2),
            "notification_preferences": {
                "email": True,
                "webhook_url": "https://example.com/webhook",
                "immediate_alerts": True
            }
        },
        "price_monitoring_workflow_input": {
            "workflow_id": "price-monitoring-456",
            "user_id": "user-456",
            "product_ids": [1, 2, 3, 4, 5],
            "monitoring_frequency": "daily",
            "price_change_threshold": 5.0,
            "monitoring_duration_days": 30,
            "alert_preferences": {
                "email_notifications": True,
                "webhook_url": "https://example.com/price-alerts",
                "immediate_alerts_threshold": 10.0,
                "daily_summary": True
            },
            "comparison_settings": {
                "compare_with_competitors": True,
                "include_historical_trends": True,
                "trend_analysis_days": 14
            }
        },
        "data_processing_workflow_input": {
            "workflow_id": "data-processing-789",
            "user_id": "user-789",
            "data_sources": [
                {
                    "type": "scraped_data",
                    "source_id": "scraping-job-123",
                    "data_format": "json",
                    "estimated_records": 1000
                },
                {
                    "type": "api_data",
                    "source_id": "api-sync-456",
                    "data_format": "xml",
                    "estimated_records": 500
                }
            ],
            "processing_options": {
                "validate_data": True,
                "deduplicate": True,
                "normalize_prices": True,
                "extract_specifications": True,
                "generate_thumbnails": True
            },
            "output_settings": {
                "store_in_database": True,
                "generate_report": True,
                "update_search_index": True,
                "notify_completion": True
            }
        },
        "invalid_workflow_input": {
            "workflow_id": "",  # Invalid: empty workflow ID
            "user_id": None,  # Invalid: null user ID
            "product_urls": [],  # Invalid: empty URL list
            "categories": ["invalid_category"],  # Invalid category
            "research_criteria": {
                "max_price": -100,  # Invalid: negative price
                "min_flow_rate": -50  # Invalid: negative flow rate
            }
        }
    }


@pytest.fixture
def sample_workflow_outputs():
    """Create sample workflow output data for testing."""
    return {
        "research_workflow_success_output": {
            "workflow_id": "research-workflow-123",
            "status": "completed",
            "execution_time_seconds": 2730,  # 45.5 minutes
            "products_found": 3,
            "products_data": [
                {
                    "name": "AquaTech Centrifugal Pump CP-100",
                    "category": "pumps",
                    "price": Decimal("1500.00"),
                    "currency": "USD",
                    "url": "https://aquatech-solutions.com/centrifugal-pump-cp-100",
                    "specifications": {
                        "flow_rate": 100,
                        "head_pressure": 45,
                        "power_consumption": 750,
                        "material": "stainless steel",
                        "certifications": ["NSF", "UL"]
                    },
                    "availability": True,
                    "lead_time_days": 14
                },
                {
                    "name": "WaterTech Pro UV Reactor UV-55R",
                    "category": "uv_reactors",
                    "price": Decimal("850.00"),
                    "currency": "USD",
                    "url": "https://watertech-pro.com/uv-reactor-uv-55r",
                    "specifications": {
                        "uv_dose": 40,
                        "flow_rate": 10,
                        "lamp_power": 55,
                        "reactor_material": "stainless steel 316L",
                        "certifications": ["NSF 55", "DVGW"]
                    },
                    "availability": True,
                    "lead_time_days": 7
                },
                {
                    "name": "Industrial Heavy-Duty Pump HD-500",
                    "category": "pumps",
                    "price": Decimal("3200.00"),
                    "currency": "USD",
                    "url": "https://industrial-pumps.com/heavy-duty-pump-hd-500",
                    "specifications": {
                        "flow_rate": 300,
                        "head_pressure": 120,
                        "power_consumption": 2200,
                        "material": "duplex stainless steel",
                        "certifications": ["API", "ASME"]
                    },
                    "availability": True,
                    "lead_time_days": 28
                }
            ],
            "report_generated": True,
            "report_url": "https://reports.ecomate.com/research-workflow-123",
            "summary_statistics": {
                "average_price": Decimal("1850.00"),
                "price_range": {
                    "min": Decimal("850.00"),
                    "max": Decimal("3200.00")
                },
                "categories_found": ["pumps", "uv_reactors"],
                "suppliers_found": ["AquaTech Solutions", "WaterTech Pro", "Industrial Pumps Inc"],
                "average_lead_time_days": 16.3
            },
            "completed_at": datetime.now(timezone.utc)
        },
        "price_monitoring_workflow_output": {
            "workflow_id": "price-monitoring-456",
            "status": "active",
            "monitoring_started_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "products_monitored": 5,
            "price_changes_detected": [
                {
                    "product_id": 1,
                    "product_name": "AquaTech Centrifugal Pump CP-100",
                    "old_price": Decimal("1500.00"),
                    "new_price": Decimal("1575.00"),
                    "change_percentage": 5.0,
                    "change_type": "increase",
                    "detected_at": datetime.now(timezone.utc) - timedelta(minutes=30)
                },
                {
                    "product_id": 3,
                    "product_name": "AquaTech Industrial UV System UV-1200I",
                    "old_price": Decimal("12500.00"),
                    "new_price": Decimal("11875.00"),
                    "change_percentage": -5.0,
                    "change_type": "decrease",
                    "detected_at": datetime.now(timezone.utc) - timedelta(minutes=15)
                }
            ],
            "alerts_sent": 2,
            "next_check_scheduled": datetime.now(timezone.utc) + timedelta(hours=23),
            "monitoring_statistics": {
                "total_checks_performed": 1,
                "successful_checks": 5,
                "failed_checks": 0,
                "average_response_time_ms": 1250,
                "significant_changes_detected": 2
            }
        },
        "data_processing_workflow_output": {
            "workflow_id": "data-processing-789",
            "status": "completed",
            "execution_time_seconds": 1800,  # 30 minutes
            "records_processed": 1500,
            "processing_results": {
                "records_validated": 1500,
                "validation_failures": 25,
                "duplicates_removed": 50,
                "prices_normalized": 1425,
                "specifications_extracted": 1400,
                "thumbnails_generated": 1350
            },
            "data_quality_metrics": {
                "completeness_score": 95.2,
                "accuracy_score": 98.1,
                "consistency_score": 96.8,
                "overall_quality_score": 96.7
            },
            "output_locations": {
                "database_records_created": 1425,
                "report_url": "https://reports.ecomate.com/data-processing-789",
                "search_index_updated": True,
                "backup_location": "s3://ecomate-backups/data-processing-789/"
            },
            "completed_at": datetime.now(timezone.utc)
        },
        "workflow_failure_output": {
            "workflow_id": "research-workflow-failed-999",
            "status": "failed",
            "execution_time_seconds": 900,  # 15 minutes before failure
            "error_details": {
                "error_type": "ScrapingError",
                "error_message": "Failed to scrape product data from multiple sources",
                "error_code": "SCRAPING_FAILED",
                "failed_urls": [
                    "https://unavailable-site.com/product1",
                    "https://blocked-site.com/product2"
                ],
                "retry_attempts": 3,
                "last_error_at": datetime.now(timezone.utc) - timedelta(minutes=5)
            },
            "partial_results": {
                "products_successfully_scraped": 1,
                "products_failed": 2,
                "data_collected": [
                    {
                        "name": "Partial Product Data",
                        "url": "https://working-site.com/product",
                        "price": Decimal("999.99")
                    }
                ]
            },
            "failed_at": datetime.now(timezone.utc)
        }
    }


@pytest.fixture
def sample_activity_inputs():
    """Create sample activity input data for testing."""
    return {
        "scrape_product_activity_input": {
            "url": "https://aquatech-solutions.com/centrifugal-pump-cp-100",
            "category": "pumps",
            "retry_count": 0,
            "timeout_seconds": 30,
            "user_agent": "EcoMate-AI/1.0 (+https://ecomate.ai/bot)",
            "headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate"
            }
        },
        "parse_product_data_activity_input": {
            "html_content": "<html><body><h1>Product Name</h1><span class='price'>$1500.00</span></body></html>",
            "url": "https://example.com/product",
            "category": "pumps",
            "parsing_rules": {
                "name_selector": "h1",
                "price_selector": ".price",
                "specifications_selector": ".specs table tr"
            }
        },
        "store_product_data_activity_input": {
            "product_data": {
                "name": "Test Product",
                "category": "pumps",
                "price": Decimal("1500.00"),
                "currency": "USD",
                "specifications": {"flow_rate": 100}
            },
            "user_id": "user-123",
            "workflow_id": "research-workflow-123"
        },
        "send_notification_activity_input": {
            "notification_type": "workflow_completed",
            "recipient": "user@example.com",
            "subject": "Research Workflow Completed",
            "message": "Your product research workflow has completed successfully.",
            "data": {
                "workflow_id": "research-workflow-123",
                "products_found": 3,
                "report_url": "https://reports.ecomate.com/research-workflow-123"
            }
        },
        "check_price_activity_input": {
            "product_id": 1,
            "current_price": Decimal("1500.00"),
            "url": "https://aquatech-solutions.com/centrifugal-pump-cp-100",
            "threshold_percentage": 5.0,
            "user_id": "user-456"
        }
    }


@pytest.fixture
def sample_activity_outputs():
    """Create sample activity output data for testing."""
    return {
        "scrape_product_activity_success_output": {
            "success": True,
            "html_content": "<html><body><h1>AquaTech Centrifugal Pump CP-100</h1><span class='price'>$1,500.00</span><div class='specs'>...</div></body></html>",
            "response_time_ms": 1250,
            "status_code": 200,
            "content_length": 15420,
            "scraped_at": datetime.now(timezone.utc)
        },
        "scrape_product_activity_failure_output": {
            "success": False,
            "error_message": "HTTP 404: Product page not found",
            "error_code": "PAGE_NOT_FOUND",
            "status_code": 404,
            "retry_recommended": False,
            "scraped_at": datetime.now(timezone.utc)
        },
        "parse_product_data_activity_output": {
            "success": True,
            "product_data": {
                "name": "AquaTech Centrifugal Pump CP-100",
                "category": "pumps",
                "price": Decimal("1500.00"),
                "currency": "USD",
                "specifications": {
                    "flow_rate": 100,
                    "head_pressure": 45,
                    "power_consumption": 750,
                    "material": "stainless steel"
                },
                "availability": True,
                "lead_time_days": 14,
                "images": [
                    "https://aquatech-solutions.com/images/cp-100-front.jpg"
                ]
            },
            "parsing_confidence": 0.95,
            "fields_extracted": 8,
            "fields_missing": 2,
            "parsed_at": datetime.now(timezone.utc)
        },
        "store_product_data_activity_output": {
            "success": True,
            "product_id": 123,
            "database_record_created": True,
            "search_index_updated": True,
            "cache_updated": True,
            "stored_at": datetime.now(timezone.utc)
        },
        "send_notification_activity_output": {
            "success": True,
            "notification_id": "notif-789",
            "delivery_method": "email",
            "delivered_at": datetime.now(timezone.utc),
            "recipient_confirmed": True
        },
        "check_price_activity_output": {
            "success": True,
            "price_changed": True,
            "old_price": Decimal("1500.00"),
            "new_price": Decimal("1575.00"),
            "change_percentage": 5.0,
            "change_type": "increase",
            "threshold_exceeded": True,
            "alert_triggered": True,
            "checked_at": datetime.now(timezone.utc)
        }
    }


@pytest.fixture
def workflow_execution_scenarios():
    """Create workflow execution scenarios for testing."""
    return {
        "success_scenarios": [
            {
                "workflow_type": "research",
                "input_size": "small",  # 1-3 products
                "expected_duration_minutes": 15,
                "expected_success_rate": 0.95
            },
            {
                "workflow_type": "research",
                "input_size": "medium",  # 4-10 products
                "expected_duration_minutes": 45,
                "expected_success_rate": 0.90
            },
            {
                "workflow_type": "research",
                "input_size": "large",  # 11-50 products
                "expected_duration_minutes": 120,
                "expected_success_rate": 0.85
            },
            {
                "workflow_type": "price_monitoring",
                "input_size": "small",  # 1-10 products
                "expected_duration_minutes": 5,
                "expected_success_rate": 0.98
            },
            {
                "workflow_type": "price_monitoring",
                "input_size": "large",  # 100+ products
                "expected_duration_minutes": 30,
                "expected_success_rate": 0.95
            }
        ],
        "failure_scenarios": [
            {
                "failure_type": "network_timeout",
                "expected_retry_count": 3,
                "recovery_possible": True
            },
            {
                "failure_type": "parsing_error",
                "expected_retry_count": 1,
                "recovery_possible": False
            },
            {
                "failure_type": "database_error",
                "expected_retry_count": 2,
                "recovery_possible": True
            },
            {
                "failure_type": "rate_limit_exceeded",
                "expected_retry_count": 5,
                "recovery_possible": True,
                "backoff_strategy": "exponential"
            }
        ],
        "performance_scenarios": [
            {
                "concurrent_workflows": 1,
                "expected_throughput": "100%"
            },
            {
                "concurrent_workflows": 5,
                "expected_throughput": "95%"
            },
            {
                "concurrent_workflows": 10,
                "expected_throughput": "85%"
            },
            {
                "concurrent_workflows": 20,
                "expected_throughput": "70%"
            }
        ]
    }


@pytest.fixture
def workflow_signal_scenarios():
    """Create workflow signal scenarios for testing."""
    return {
        "pause_resume_signals": [
            {"signal_name": "pause_workflow", "expected_state": "paused"},
            {"signal_name": "resume_workflow", "expected_state": "running"}
        ],
        "priority_change_signals": [
            {"signal_name": "set_high_priority", "new_priority": "high"},
            {"signal_name": "set_low_priority", "new_priority": "low"}
        ],
        "configuration_update_signals": [
            {
                "signal_name": "update_monitoring_frequency",
                "new_config": {"frequency": "hourly"}
            },
            {
                "signal_name": "update_price_threshold",
                "new_config": {"threshold": 10.0}
            }
        ],
        "cancellation_signals": [
            {"signal_name": "cancel_workflow", "reason": "user_requested"},
            {"signal_name": "emergency_stop", "reason": "system_maintenance"}
        ]
    }


@pytest.fixture
def workflow_query_scenarios():
    """Create workflow query scenarios for testing."""
    return {
        "status_queries": [
            {"query_name": "get_workflow_status", "expected_fields": ["status", "progress", "current_step"]},
            {"query_name": "get_execution_metrics", "expected_fields": ["duration", "activities_completed", "errors_encountered"]}
        ],
        "progress_queries": [
            {"query_name": "get_progress_percentage", "expected_type": "float"},
            {"query_name": "get_current_activity", "expected_type": "string"},
            {"query_name": "get_estimated_completion", "expected_type": "datetime"}
        ],
        "data_queries": [
            {"query_name": "get_partial_results", "expected_type": "dict"},
            {"query_name": "get_error_details", "expected_type": "dict"},
            {"query_name": "get_activity_history", "expected_type": "list"}
        ]
    }