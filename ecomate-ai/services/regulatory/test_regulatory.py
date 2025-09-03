"""Comprehensive tests for regulatory monitor service."""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from .client import RegulatoryClient, RegulatoryAPIError
from .service import RegulatoryService
from .models import (
    StandardsBody,
    RegulatoryStandard,
    ComplianceCheck,
    ComplianceStatus,
    RegulatoryAlert,
    StandardsUpdate,
    ComplianceReport,
    RegulatoryQuery,
    RegulatoryResponse,
    BatchRegulatoryRequest,
    BatchRegulatoryResponse,
    StandardCategory,
    AlertSeverity,
    UpdateType
)


class TestRegulatoryClient:
    """Test cases for RegulatoryClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return RegulatoryClient()
    
    @pytest.fixture
    def mock_standard(self):
        """Create mock regulatory standard."""
        return RegulatoryStandard(
            id="ISO-27001",
            title="Information Security Management Systems",
            body=StandardsBody.ISO,
            category=StandardCategory.SECURITY,
            version="2013",
            status="active",
            publication_date=date(2013, 10, 1),
            last_updated=date(2022, 2, 15),
            description="Requirements for establishing, implementing, maintaining and continually improving an information security management system.",
            scope="Information security management",
            keywords=["information security", "ISMS", "cybersecurity"],
            url="https://www.iso.org/standard/54534.html",
            document_type="standard",
            language="en",
            pages=23,
            price=158.0,
            currency="CHF"
        )
    
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.session is None
        assert client.config == {}
        assert client._cache == {}
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test client context manager."""
        async with client:
            assert client.session is not None
        assert client.session is None
    
    @pytest.mark.asyncio
    async def test_get_standard_success(self, client, mock_standard):
        """Test successful standard retrieval."""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_standard.dict()
            
            async with client:
                result = await client.get_standard(StandardsBody.ISO, "ISO-27001")
            
            assert result == mock_standard
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_standard_not_found(self, client):
        """Test standard not found."""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = RegulatoryAPIError("Standard not found", 404)
            
            async with client:
                result = await client.get_standard(StandardsBody.ISO, "INVALID")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_search_standards(self, client, mock_standard):
        """Test standards search."""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [mock_standard.dict()]
            
            async with client:
                results = await client.search_standards(
                    StandardsBody.ISO,
                    "security",
                    StandardCategory.SECURITY
                )
            
            assert len(results) == 1
            assert results[0] == mock_standard
    
    @pytest.mark.asyncio
    async def test_get_standards_updates(self, client):
        """Test getting standards updates."""
        mock_update = StandardsUpdate(
            id="update_1",
            standard_id="ISO-27001",
            body=StandardsBody.ISO,
            update_type=UpdateType.REVISION,
            title="ISO 27001:2022 Published",
            description="New version of ISO 27001 published",
            publication_date=date.today(),
            effective_date=date.today() + timedelta(days=90),
            url="https://example.com/update",
            impact_level="medium",
            affected_clauses=["4.1", "4.2"],
            summary="Updated requirements for context of organization"
        )
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [mock_update.dict()]
            
            async with client:
                results = await client.get_standards_updates(
                    StandardsBody.ISO,
                    date.today() - timedelta(days=30)
                )
            
            assert len(results) == 1
            assert results[0] == mock_update
    
    @pytest.mark.asyncio
    async def test_get_alerts(self, client):
        """Test getting regulatory alerts."""
        mock_alert = RegulatoryAlert(
            id="alert_1",
            title="New EPA Regulation",
            message="New environmental regulation published",
            severity=AlertSeverity.MEDIUM,
            body=StandardsBody.EPA,
            standard_id="EPA-40CFR",
            alert_type="new_regulation",
            created_at=datetime.utcnow(),
            affected_entities=["entity_1"],
            action_required=True,
            action_deadline=date.today() + timedelta(days=60),
            url="https://epa.gov/regulation",
            tags=["environmental", "compliance"]
        )
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [mock_alert.dict()]
            
            async with client:
                results = await client.get_alerts(
                    AlertSeverity.MEDIUM,
                    date.today() - timedelta(days=7)
                )
            
            assert len(results) == 1
            assert results[0] == mock_alert
    
    @pytest.mark.asyncio
    async def test_request_caching(self, client):
        """Test request caching functionality."""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"test": "data"}
            
            async with client:
                # First request
                result1 = await client._make_request("GET", "test_url")
                # Second request (should use cache)
                result2 = await client._make_request("GET", "test_url")
            
            assert result1 == result2
            # Should only make one actual request due to caching
            mock_request.assert_called_once()


class TestRegulatoryService:
    """Test cases for RegulatoryService."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock(spec=RegulatoryClient)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def service(self, mock_client):
        """Create test service."""
        return RegulatoryService(mock_client)
    
    @pytest.fixture
    def mock_standard(self):
        """Create mock standard."""
        return RegulatoryStandard(
            id="SANS-20",
            title="Critical Security Controls",
            body=StandardsBody.SANS,
            category=StandardCategory.SECURITY,
            version="8.0",
            status="active",
            publication_date=date(2021, 5, 18),
            last_updated=date(2021, 5, 18),
            description="Critical security controls for effective cyber defense",
            scope="Cybersecurity controls",
            keywords=["security controls", "cybersecurity", "defense"],
            url="https://www.sans.org/controls",
            document_type="framework",
            language="en"
        )
    
    @pytest.mark.asyncio
    async def test_monitor_compliance_success(self, service, mock_client, mock_standard):
        """Test successful compliance monitoring."""
        mock_client.get_standard.return_value = mock_standard
        
        result = await service.monitor_compliance(
            entity_id="test_entity",
            standards=["SANS-20"],
            check_interval=3600
        )
        
        assert result["entity_id"] == "test_entity"
        assert "overall_status" in result
        assert "standards_checked" in result
        assert "results" in result
        assert "next_check" in result
    
    @pytest.mark.asyncio
    async def test_monitor_compliance_error(self, service, mock_client):
        """Test compliance monitoring with error."""
        mock_client.get_standard.side_effect = Exception("API Error")
        
        result = await service.monitor_compliance(
            entity_id="test_entity",
            standards=["INVALID"],
            check_interval=3600
        )
        
        assert "error" in result
        assert result["entity_id"] == "test_entity"
    
    @pytest.mark.asyncio
    async def test_track_standards_updates(self, service, mock_client):
        """Test tracking standards updates."""
        mock_update = StandardsUpdate(
            id="update_1",
            standard_id="SANS-20",
            body=StandardsBody.SANS,
            update_type=UpdateType.REVISION,
            title="SANS Controls Updated",
            description="Updated security controls",
            publication_date=date.today(),
            effective_date=date.today() + timedelta(days=30),
            url="https://sans.org/update",
            impact_level="high",
            affected_clauses=["1.1", "1.2"],
            summary="Major updates to controls"
        )
        
        mock_client.get_standards_updates.return_value = [mock_update]
        
        results = await service.track_standards_updates(
            bodies=[StandardsBody.SANS],
            since=date.today() - timedelta(days=30)
        )
        
        assert len(results) == 1
        assert results[0] == mock_update
    
    @pytest.mark.asyncio
    async def test_generate_compliance_report(self, service):
        """Test compliance report generation."""
        report = await service.generate_compliance_report(
            entity_id="test_entity",
            entity_name="Test Entity",
            period_start=date.today() - timedelta(days=90),
            period_end=date.today()
        )
        
        assert isinstance(report, ComplianceReport)
        assert report.entity_id == "test_entity"
        assert report.entity_name == "Test Entity"
        assert report.overall_status in [ComplianceStatus.COMPLIANT, ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT]
    
    @pytest.mark.asyncio
    async def test_get_regulatory_alerts(self, service, mock_client):
        """Test getting regulatory alerts."""
        mock_alert = RegulatoryAlert(
            id="alert_1",
            title="Test Alert",
            message="Test alert message",
            severity=AlertSeverity.HIGH,
            body=StandardsBody.ISO,
            standard_id="ISO-27001",
            alert_type="compliance_violation",
            created_at=datetime.utcnow(),
            affected_entities=["test_entity"],
            action_required=True
        )
        
        mock_client.get_alerts.return_value = [mock_alert]
        
        results = await service.get_regulatory_alerts(
            entity_id="test_entity",
            severity=AlertSeverity.HIGH
        )
        
        assert len(results) == 1
        assert results[0] == mock_alert
    
    @pytest.mark.asyncio
    async def test_assess_regulatory_impact(self, service):
        """Test regulatory impact assessment."""
        proposed_changes = [
            {
                "type": "process_change",
                "description": "New chemical process implementation",
                "scope": ["ISO-14001", "EPA-40CFR"]
            }
        ]
        
        result = await service.assess_regulatory_impact(
            entity_id="test_entity",
            proposed_changes=proposed_changes
        )
        
        assert result["entity_id"] == "test_entity"
        assert "overall_risk" in result
        assert "changes_assessed" in result
        assert "impact_results" in result
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_process_query_search_standards(self, service, mock_client, mock_standard):
        """Test processing search standards query."""
        mock_client.search_standards.return_value = [mock_standard]
        
        query = RegulatoryQuery(
            query_type="search_standards",
            keywords=["security"],
            body=StandardsBody.SANS,
            category=StandardCategory.SECURITY,
            limit=10
        )
        
        response = await service.process_query(query)
        
        assert response.success is True
        assert len(response.data) == 1
        assert response.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_process_query_invalid_type(self, service):
        """Test processing query with invalid type."""
        query = RegulatoryQuery(
            query_type="invalid_type",
            limit=10
        )
        
        response = await service.process_query(query)
        
        assert response.success is False
        assert "Unknown query type" in response.message
    
    @pytest.mark.asyncio
    async def test_process_batch_request(self, service, mock_client, mock_standard):
        """Test processing batch requests."""
        mock_client.search_standards.return_value = [mock_standard]
        
        queries = [
            RegulatoryQuery(
                query_type="search_standards",
                keywords=["security"],
                limit=5
            ),
            RegulatoryQuery(
                query_type="search_standards",
                keywords=["environmental"],
                limit=5
            )
        ]
        
        batch_request = BatchRegulatoryRequest(
            batch_id="test_batch",
            requests=queries
        )
        
        response = await service.process_batch_request(batch_request)
        
        assert response.batch_id == "test_batch"
        assert response.total_requests == 2
        assert response.batch_status == "completed"
        assert len(response.responses) == 2
    
    def test_add_handlers(self, service):
        """Test adding alert and update handlers."""
        alert_handler = Mock()
        update_handler = Mock()
        
        service.add_alert_handler(alert_handler)
        service.add_update_handler(update_handler)
        
        assert alert_handler in service._alert_handlers
        assert update_handler in service._update_handlers
    
    def test_determine_standards_body(self, service):
        """Test standards body determination."""
        assert service._determine_standards_body("SANS-20") == StandardsBody.SANS
        assert service._determine_standards_body("ISO-27001") == StandardsBody.ISO
        assert service._determine_standards_body("EPA-40CFR") == StandardsBody.EPA
        assert service._determine_standards_body("OSHA-1910") == StandardsBody.OSHA
        assert service._determine_standards_body("ANSI-X9") == StandardsBody.ANSI
        assert service._determine_standards_body("ASTM-D1234") == StandardsBody.ASTM
        assert service._determine_standards_body("IEC-61508") == StandardsBody.IEC
        assert service._determine_standards_body("IEEE-802") == StandardsBody.IEEE
        assert service._determine_standards_body("UNKNOWN") is None


class TestRegulatoryModels:
    """Test cases for regulatory models."""
    
    def test_regulatory_standard_validation(self):
        """Test RegulatoryStandard validation."""
        standard = RegulatoryStandard(
            id="ISO-27001",
            title="Information Security Management",
            body=StandardsBody.ISO,
            category=StandardCategory.SECURITY,
            version="2013",
            status="active",
            publication_date=date(2013, 10, 1),
            last_updated=date(2022, 2, 15),
            description="ISMS requirements",
            scope="Information security",
            keywords=["security", "ISMS"],
            url="https://iso.org/27001",
            document_type="standard",
            language="en"
        )
        
        assert standard.id == "ISO-27001"
        assert standard.body == StandardsBody.ISO
        assert standard.category == StandardCategory.SECURITY
    
    def test_compliance_check_validation(self):
        """Test ComplianceCheck validation."""
        check = ComplianceCheck(
            id="check_1",
            requirement_id="ISO-27001",
            entity_id="entity_1",
            status=ComplianceStatus.COMPLIANT,
            check_date=datetime.utcnow(),
            assessor="Test Assessor",
            score=0.95,
            findings=["All requirements met"],
            recommendations=["Continue monitoring"],
            next_check_date=date.today() + timedelta(days=90)
        )
        
        assert check.status == ComplianceStatus.COMPLIANT
        assert 0.0 <= check.score <= 1.0
    
    def test_regulatory_alert_validation(self):
        """Test RegulatoryAlert validation."""
        alert = RegulatoryAlert(
            id="alert_1",
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.HIGH,
            body=StandardsBody.EPA,
            standard_id="EPA-40CFR",
            alert_type="new_regulation",
            created_at=datetime.utcnow(),
            affected_entities=["entity_1"],
            action_required=True
        )
        
        assert alert.severity == AlertSeverity.HIGH
        assert alert.action_required is True
    
    def test_compliance_report_validation(self):
        """Test ComplianceReport validation."""
        report = ComplianceReport(
            id="report_1",
            title="Test Report",
            entity_id="entity_1",
            entity_name="Test Entity",
            report_date=date.today(),
            period_start=date.today() - timedelta(days=90),
            period_end=date.today(),
            overall_status=ComplianceStatus.COMPLIANT,
            overall_score=0.85,
            standards_assessed=["ISO-27001"],
            checks_performed=10,
            compliant_checks=8,
            non_compliant_checks=2,
            findings=["Minor issues found"],
            recommendations=["Address findings"],
            action_items=["Update procedures"],
            next_assessment_date=date.today() + timedelta(days=90),
            assessor="Test Assessor"
        )
        
        assert 0.0 <= report.overall_score <= 1.0
        assert report.checks_performed == report.compliant_checks + report.non_compliant_checks
    
    def test_regulatory_query_validation(self):
        """Test RegulatoryQuery validation."""
        query = RegulatoryQuery(
            query_type="search_standards",
            keywords=["security", "management"],
            body=StandardsBody.ISO,
            category=StandardCategory.SECURITY,
            limit=20,
            offset=0
        )
        
        assert query.query_type == "search_standards"
        assert len(query.keywords) == 2
        assert query.limit == 20
    
    def test_batch_request_validation(self):
        """Test BatchRegulatoryRequest validation."""
        queries = [
            RegulatoryQuery(query_type="search_standards", limit=10),
            RegulatoryQuery(query_type="get_updates", limit=5)
        ]
        
        batch_request = BatchRegulatoryRequest(
            batch_id="batch_1",
            requests=queries
        )
        
        assert batch_request.batch_id == "batch_1"
        assert len(batch_request.requests) == 2


# Integration tests

class TestRegulatoryIntegration:
    """Integration tests for regulatory service."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_compliance_monitoring(self):
        """Test end-to-end compliance monitoring workflow."""
        # This would be a full integration test
        # For now, just test that components work together
        
        client = RegulatoryClient()
        service = RegulatoryService(client)
        
        # Test basic service functionality
        assert service.client == client
        assert service._compliance_cache == {}
    
    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """Test error handling across service layers."""
        client = Mock(spec=RegulatoryClient)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.get_standard.side_effect = RegulatoryAPIError("API Error", 500)
        
        service = RegulatoryService(client)
        
        result = await service.monitor_compliance(
            entity_id="test_entity",
            standards=["TEST-001"]
        )
        
        # Should handle error gracefully
        assert "error" in result or "overall_status" in result


# Performance tests

class TestRegulatoryPerformance:
    """Performance tests for regulatory service."""
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self):
        """Test batch processing performance."""
        client = Mock(spec=RegulatoryClient)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.search_standards.return_value = []
        
        service = RegulatoryService(client)
        
        # Create large batch request
        queries = [
            RegulatoryQuery(query_type="search_standards", limit=1)
            for _ in range(50)
        ]
        
        batch_request = BatchRegulatoryRequest(
            batch_id="perf_test",
            requests=queries
        )
        
        start_time = datetime.utcnow()
        response = await service.process_batch_request(batch_request)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        assert response.total_requests == 50
        assert processing_time < 10.0  # Should complete within 10 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_compliance_checks(self):
        """Test concurrent compliance checking performance."""
        client = Mock(spec=RegulatoryClient)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.get_standard.return_value = None
        
        service = RegulatoryService(client)
        
        # Run multiple compliance checks concurrently
        tasks = [
            service.monitor_compliance(f"entity_{i}", ["TEST-001"])
            for i in range(10)
        ]
        
        start_time = datetime.utcnow()
        results = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        assert len(results) == 10
        assert processing_time < 5.0  # Should complete within 5 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])