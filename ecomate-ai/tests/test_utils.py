"""Test utilities and helper functions for EcoMate AI testing.

This module provides utility functions to support testing across
all services and components in the EcoMate AI system.
"""

import json
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


class DataManagerHelper:
    """Manages test data creation and cleanup."""
    
    def __init__(self):
        self.created_objects = []
        self.temp_files = []
    
    def create_temp_file(self, content: str, suffix: str = ".json") -> Path:
        """Create a temporary file with content."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def cleanup(self):
        """Clean up all created test data."""
        for file_path in self.temp_files:
            try:
                file_path.unlink()
            except FileNotFoundError:
                pass
        
        self.created_objects.clear()
        self.temp_files.clear()


class APIHelper:
    """Helper class for API testing."""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def assert_response_success(self, response, expected_status: int = 200):
        """Assert that a response is successful."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    
    def assert_response_error(self, response, expected_status: int = 400):
        """Assert that a response is an error."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    
    def test_endpoint_health(self, endpoint: str) -> Dict[str, Any]:
        """Test that an endpoint is healthy."""
        response = self.client.get(f"{endpoint}/health")
        return self.assert_response_success(response)
    
    def test_endpoint_crud(self, endpoint: str, create_data: Dict[str, Any], 
                          update_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Test CRUD operations on an endpoint."""
        results = {}
        
        # Test CREATE
        response = self.client.post(endpoint, json=create_data)
        created = self.assert_response_success(response, 201)
        results['create'] = 'passed'
        
        # Extract ID from created object
        object_id = created.get('id') or created.get('_id')
        assert object_id, "Created object should have an ID"
        
        # Test READ
        response = self.client.get(f"{endpoint}/{object_id}")
        retrieved = self.assert_response_success(response)
        results['read'] = 'passed'
        
        # Test UPDATE (if update data provided)
        if update_data:
            response = self.client.put(f"{endpoint}/{object_id}", json=update_data)
            updated = self.assert_response_success(response)
            results['update'] = 'passed'
        
        # Test DELETE
        response = self.client.delete(f"{endpoint}/{object_id}")
        self.assert_response_success(response, 204)
        results['delete'] = 'passed'
        
        # Verify deletion
        response = self.client.get(f"{endpoint}/{object_id}")
        self.assert_response_error(response, 404)
        results['verify_delete'] = 'passed'
        
        return results


class DataGenerator:
    """Generates mock data for testing."""
    
    @staticmethod
    def generate_html_table(headers: List[str], rows: List[List[str]], 
                           table_class: str = "data-table") -> str:
        """Generate HTML table for parser testing."""
        html = f'<table class="{table_class}">\n<thead>\n<tr>\n'
        for header in headers:
            html += f'<th>{header}</th>\n'
        html += '</tr>\n</thead>\n<tbody>\n'
        
        for row in rows:
            html += '<tr>\n'
            for cell in row:
                html += f'<td>{cell}</td>\n'
            html += '</tr>\n'
        
        html += '</tbody>\n</table>'
        return html
    
    @staticmethod
    def generate_json_response(data: Dict[str, Any], status: str = "success") -> str:
        """Generate JSON response for API testing."""
        response = {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        return json.dumps(response, indent=2)
    
    @staticmethod
    def generate_csv_data(headers: List[str], rows: List[List[str]]) -> str:
        """Generate CSV data for parser testing."""
        csv_lines = [','.join(headers)]
        for row in rows:
            csv_lines.append(','.join(str(cell) for cell in row))
        return '\n'.join(csv_lines)
    
    @staticmethod
    def generate_xml_data(root_tag: str, items: List[Dict[str, Any]]) -> str:
        """Generate XML data for parser testing."""
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<{root_tag}>\n'
        
        for item in items:
            xml += '  <item>\n'
            for key, value in item.items():
                xml += f'    <{key}>{value}</{key}>\n'
            xml += '  </item>\n'
        
        xml += f'</{root_tag}>'
        return xml


class DatabaseHelper:
    """Helper for database testing."""
    
    def __init__(self, session):
        self.session = session
    
    def create_and_commit(self, model_class, **kwargs):
        """Create and commit a database object."""
        obj = model_class(**kwargs)
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj
    
    def count_records(self, model_class) -> int:
        """Count records in a table."""
        return self.session.query(model_class).count()
    
    def clear_table(self, model_class):
        """Clear all records from a table."""
        self.session.query(model_class).delete()
        self.session.commit()


class WorkflowHelper:
    """Helper for testing Temporal workflows."""
    
    @staticmethod
    def create_mock_workflow_client():
        """Create a mock Temporal workflow client."""
        client = Mock()
        
        # Mock workflow handle
        handle = Mock()
        handle.result = Mock(return_value={"status": "completed"})
        handle.query = Mock(return_value={"state": "running"})
        handle.signal = Mock()
        handle.cancel = Mock()
        
        client.start_workflow = Mock(return_value=handle)
        client.get_workflow_handle = Mock(return_value=handle)
        
        return client, handle
    
    @staticmethod
    def simulate_workflow_execution(workflow_func, input_data: Dict[str, Any], 
                                  duration_seconds: float = 1.0) -> Dict[str, Any]:
        """Simulate workflow execution with timing."""
        start_time = time.time()
        
        # Simulate processing time
        time.sleep(min(duration_seconds, 0.1))  # Cap at 0.1s for tests
        
        result = {
            "status": "completed",
            "input": input_data,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return result


class PerformanceHelper:
    """Helper for performance testing."""
    
    def __init__(self):
        self.measurements = []
    
    def measure_execution_time(self, func, *args, **kwargs) -> float:
        """Measure function execution time."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        self.measurements.append({
            'function': func.__name__,
            'execution_time': execution_time,
            'timestamp': datetime.now(timezone.utc)
        })
        
        return execution_time
    
    def assert_performance_threshold(self, func, threshold_seconds: float, 
                                   *args, **kwargs):
        """Assert that function executes within time threshold."""
        execution_time = self.measure_execution_time(func, *args, **kwargs)
        assert execution_time <= threshold_seconds, f"Function {func.__name__} took {execution_time:.3f}s, expected <= {threshold_seconds}s"
    
    def get_average_execution_time(self, function_name: str) -> float:
        """Get average execution time for a function."""
        times = [m['execution_time'] for m in self.measurements if m['function'] == function_name]
        return sum(times) / len(times) if times else 0.0


class ValidationHelper:
    """Helper for validation testing."""
    
    @staticmethod
    def assert_valid_uuid(value: str):
        """Assert that a value is a valid UUID."""
        import uuid
        try:
            uuid.UUID(value)
        except ValueError:
            pytest.fail(f"'{value}' is not a valid UUID")
    
    @staticmethod
    def assert_valid_email(email: str):
        """Assert that a value is a valid email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(pattern, email), f"'{email}' is not a valid email address"
    
    @staticmethod
    def assert_valid_url(url: str):
        """Assert that a value is a valid URL."""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        assert re.match(pattern, url), f"'{url}' is not a valid URL"
    
    @staticmethod
    def assert_valid_phone(phone: str):
        """Assert that a value is a valid phone number."""
        import re
        # Simple phone validation - can be enhanced
        pattern = r'^[+]?[1-9]?[0-9]{7,15}$'
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        assert re.match(pattern, cleaned_phone), f"'{phone}' is not a valid phone number"
    
    @staticmethod
    def assert_date_range(date_value: datetime, start_date: datetime, end_date: datetime):
        """Assert that a date is within a specified range."""
        assert start_date <= date_value <= end_date, f"Date {date_value} is not between {start_date} and {end_date}"
    
    @staticmethod
    def assert_numeric_range(value: Union[int, float], min_value: Union[int, float], 
                           max_value: Union[int, float]):
        """Assert that a numeric value is within a specified range."""
        assert min_value <= value <= max_value, f"Value {value} is not between {min_value} and {max_value}"


class IntegrationHelper:
    """Helper for integration testing."""
    
    def __init__(self, api_client: TestClient):
        self.api_client = api_client
        self.api_helper = APIHelper(api_client)
    
    def test_service_health_checks(self, services: List[str]) -> Dict[str, str]:
        """Test health checks for multiple services."""
        results = {}
        
        for service in services:
            try:
                health_data = self.api_helper.test_endpoint_health(f"/{service}")
                results[service] = "healthy" if health_data.get("status") == "ok" else "unhealthy"
            except Exception as e:
                results[service] = f"error: {str(e)}"
        
        return results
    
    def test_service_integration_flow(self, flow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test an integration flow across multiple services."""
        results = {
            "steps": [],
            "overall_status": "success",
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            for step in flow_config.get("steps", []):
                step_result = self._execute_integration_step(step)
                results["steps"].append(step_result)
                
                if step_result["status"] != "success":
                    results["overall_status"] = "failed"
                    break
        
        except Exception as e:
            results["overall_status"] = "error"
            results["error"] = str(e)
        
        finally:
            results["execution_time"] = time.time() - start_time
        
        return results
    
    def _execute_integration_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single integration test step."""
        method = step.get("method", "GET").upper()
        endpoint = step.get("endpoint")
        data = step.get("data")
        expected_status = step.get("expected_status", 200)
        
        try:
            if method == "GET":
                response = self.api_client.get(endpoint)
            elif method == "POST":
                response = self.api_client.post(endpoint, json=data)
            elif method == "PUT":
                response = self.api_client.put(endpoint, json=data)
            elif method == "DELETE":
                response = self.api_client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return {
                "step": step.get("name", f"{method} {endpoint}"),
                "status": "success" if response.status_code == expected_status else "failed",
                "response_status": response.status_code,
                "expected_status": expected_status
            }
        
        except Exception as e:
            return {
                "step": step.get("name", f"{method} {endpoint}"),
                "status": "error",
                "error": str(e)
            }


# Utility functions

def wait_for_condition(condition_func, timeout_seconds: float = 10.0, 
                      check_interval: float = 0.1) -> bool:
    """Wait for a condition to become true."""
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if condition_func():
            return True
        time.sleep(check_interval)
    
    return False


def generate_test_id(prefix: str = "test") -> str:
    """Generate a unique test ID."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_test_file_content(file_type: str, **kwargs) -> str:
    """Create test file content based on type."""
    generator = MockDataGenerator()
    
    if file_type == "html_table":
        headers = kwargs.get("headers", ["Name", "Value"])
        rows = kwargs.get("rows", [["Test", "123"]])
        return generator.generate_html_table(headers, rows)
    
    elif file_type == "json":
        data = kwargs.get("data", {"test": "data"})
        return generator.generate_json_response(data)
    
    elif file_type == "csv":
        headers = kwargs.get("headers", ["Name", "Value"])
        rows = kwargs.get("rows", [["Test", "123"]])
        return generator.generate_csv_data(headers, rows)
    
    elif file_type == "xml":
        root_tag = kwargs.get("root_tag", "data")
        items = kwargs.get("items", [{"name": "Test", "value": "123"}])
        return generator.generate_xml_data(root_tag, items)
    
    else:
        return f"Test content for {file_type}"


def assert_test_coverage_threshold(coverage_data: Dict[str, float], 
                                 threshold: float = 80.0):
    """Assert that test coverage meets threshold."""
    for module, coverage in coverage_data.items():
        assert coverage >= threshold, f"Module {module} has {coverage}% coverage, expected >= {threshold}%"


def cleanup_test_environment():
    """Clean up test environment after test execution."""
    # This would clean up any global test state
    # Implementation depends on specific cleanup needs
    pass