"""Integration tests for the Proposal Service.

These tests verify the proposal service API endpoints work correctly
with realistic data and proper error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from tests.test_utils import APITestHelper, IntegrationHelper
from tests.factories import create_test_proposal, create_test_product


class TestProposalServiceIntegration:
    """Integration tests for proposal service endpoints."""
    
    def test_proposal_service_health(self, sample_api_client):
        """Test proposal service health endpoint."""
        api_helper = APITestHelper(sample_api_client)
        
        # Test health endpoint
        response = sample_api_client.get("/proposal/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "ok"
        assert "timestamp" in health_data
        assert "service" in health_data
        assert health_data["service"] == "proposal"
    
    def test_create_proposal_success(self, sample_api_client, mock_database, mock_env_vars):
        """Test successful proposal creation."""
        # Create test proposal data
        proposal_data = create_test_proposal(
            title="Water Treatment System Proposal",
            project_type="water_treatment",
            budget_usd=50000.0
        )
        
        # Remove server-generated fields for creation
        create_data = {k: v for k, v in proposal_data.items() 
                      if k not in ['id', 'created_at', 'updated_at', 'total_cost']}
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            # Mock service response
            mock_service.return_value.create_proposal.return_value = proposal_data
            
            response = sample_api_client.post("/proposal/proposals", json=create_data)
            
            assert response.status_code == 201
            created_proposal = response.json()
            
            assert created_proposal["title"] == proposal_data["title"]
            assert created_proposal["project_type"] == proposal_data["project_type"]
            assert created_proposal["budget_usd"] == proposal_data["budget_usd"]
            assert "id" in created_proposal
            assert "created_at" in created_proposal
    
    def test_get_proposal_success(self, sample_api_client, mock_database):
        """Test successful proposal retrieval."""
        proposal_data = create_test_proposal()
        proposal_id = proposal_data["id"]
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.get_proposal.return_value = proposal_data
            
            response = sample_api_client.get(f"/proposal/proposals/{proposal_id}")
            
            assert response.status_code == 200
            retrieved_proposal = response.json()
            
            assert retrieved_proposal["id"] == proposal_id
            assert retrieved_proposal["title"] == proposal_data["title"]
            assert retrieved_proposal["status"] == proposal_data["status"]
    
    def test_get_proposal_not_found(self, sample_api_client, mock_database):
        """Test proposal retrieval with non-existent ID."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.get_proposal.return_value = None
            
            response = sample_api_client.get(f"/proposal/proposals/{non_existent_id}")
            
            assert response.status_code == 404
            error_data = response.json()
            assert "detail" in error_data
            assert "not found" in error_data["detail"].lower()
    
    def test_list_proposals_success(self, sample_api_client, mock_database):
        """Test successful proposal listing with pagination."""
        # Create test proposals
        proposals = [create_test_proposal() for _ in range(5)]
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.list_proposals.return_value = {
                "proposals": proposals[:3],  # First page
                "total": 5,
                "page": 1,
                "per_page": 3,
                "pages": 2
            }
            
            response = sample_api_client.get("/proposal/proposals?page=1&per_page=3")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["proposals"]) == 3
            assert data["total"] == 5
            assert data["page"] == 1
            assert data["per_page"] == 3
            assert data["pages"] == 2
    
    def test_update_proposal_success(self, sample_api_client, mock_database):
        """Test successful proposal update."""
        original_proposal = create_test_proposal(status="draft")
        proposal_id = original_proposal["id"]
        
        update_data = {
            "status": "submitted",
            "title": "Updated Water Treatment Proposal"
        }
        
        updated_proposal = {**original_proposal, **update_data}
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.update_proposal.return_value = updated_proposal
            
            response = sample_api_client.put(f"/proposal/proposals/{proposal_id}", json=update_data)
            
            assert response.status_code == 200
            updated = response.json()
            
            assert updated["id"] == proposal_id
            assert updated["status"] == "submitted"
            assert updated["title"] == "Updated Water Treatment Proposal"
    
    def test_delete_proposal_success(self, sample_api_client, mock_database):
        """Test successful proposal deletion."""
        proposal_data = create_test_proposal()
        proposal_id = proposal_data["id"]
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.delete_proposal.return_value = True
            
            response = sample_api_client.delete(f"/proposal/proposals/{proposal_id}")
            
            assert response.status_code == 204
    
    def test_generate_proposal_from_requirements(self, sample_api_client, mock_database, mock_external_apis):
        """Test proposal generation from requirements."""
        requirements = {
            "project_type": "water_treatment",
            "flow_rate_lpm": 1000,
            "treatment_goals": ["disinfection", "filtration"],
            "budget_range": {"min": 30000, "max": 80000},
            "location": "New York, NY",
            "timeline_months": 6
        }
        
        # Mock generated proposal
        generated_proposal = create_test_proposal(
            title="AI-Generated Water Treatment Proposal",
            project_type="water_treatment",
            budget_usd=65000.0,
            components=[
                {"product_id": "pump-001", "quantity": 2, "unit_price": 5000},
                {"product_id": "uv-001", "quantity": 1, "unit_price": 15000},
                {"product_id": "filter-001", "quantity": 3, "unit_price": 3000}
            ]
        )
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.generate_proposal.return_value = generated_proposal
            
            response = sample_api_client.post("/proposal/generate", json=requirements)
            
            assert response.status_code == 201
            proposal = response.json()
            
            assert proposal["project_type"] == "water_treatment"
            assert "components" in proposal
            assert len(proposal["components"]) > 0
            assert "total_cost" in proposal
    
    def test_proposal_cost_calculation(self, sample_api_client, mock_database):
        """Test proposal cost calculation endpoint."""
        proposal_data = create_test_proposal()
        proposal_id = proposal_data["id"]
        
        cost_breakdown = {
            "components_cost": 45000.0,
            "labor_cost": 8000.0,
            "materials_cost": 3000.0,
            "overhead_cost": 4000.0,
            "total_cost": 60000.0,
            "margin_percent": 15.0
        }
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            mock_service.return_value.calculate_costs.return_value = cost_breakdown
            
            response = sample_api_client.get(f"/proposal/proposals/{proposal_id}/costs")
            
            assert response.status_code == 200
            costs = response.json()
            
            assert costs["total_cost"] == 60000.0
            assert costs["components_cost"] == 45000.0
            assert "margin_percent" in costs
    
    def test_proposal_validation_errors(self, sample_api_client):
        """Test proposal validation with invalid data."""
        invalid_data = {
            "title": "",  # Empty title
            "budget_usd": -1000,  # Negative budget
            "project_type": "invalid_type",  # Invalid project type
            "components": []  # Empty components
        }
        
        response = sample_api_client.post("/proposal/proposals", json=invalid_data)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        
        # Check that validation errors are returned
        errors = error_data["detail"]
        assert any("title" in str(error) for error in errors)
        assert any("budget_usd" in str(error) for error in errors)
    
    def test_proposal_service_error_handling(self, sample_api_client, mock_database):
        """Test proposal service error handling."""
        proposal_id = "test-proposal-id"
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            # Simulate service error
            mock_service.return_value.get_proposal.side_effect = Exception("Database connection failed")
            
            response = sample_api_client.get(f"/proposal/proposals/{proposal_id}")
            
            assert response.status_code == 500
            error_data = response.json()
            assert "detail" in error_data
    
    @pytest.mark.slow
    def test_proposal_integration_flow(self, sample_api_client, mock_database, mock_external_apis):
        """Test complete proposal workflow integration."""
        integration_helper = IntegrationTestHelper(sample_api_client)
        
        # Define integration flow
        flow_config = {
            "steps": [
                {
                    "name": "Check service health",
                    "method": "GET",
                    "endpoint": "/proposal/health",
                    "expected_status": 200
                },
                {
                    "name": "Generate proposal",
                    "method": "POST",
                    "endpoint": "/proposal/generate",
                    "data": {
                        "project_type": "water_treatment",
                        "flow_rate_lpm": 500,
                        "budget_range": {"min": 20000, "max": 50000}
                    },
                    "expected_status": 201
                },
                {
                    "name": "List proposals",
                    "method": "GET",
                    "endpoint": "/proposal/proposals",
                    "expected_status": 200
                }
            ]
        }
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            # Mock all service methods
            mock_service.return_value.generate_proposal.return_value = create_test_proposal()
            mock_service.return_value.list_proposals.return_value = {
                "proposals": [create_test_proposal()],
                "total": 1,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            # Execute integration flow
            results = integration_helper.test_service_integration_flow(flow_config)
            
            assert results["overall_status"] == "success"
            assert len(results["steps"]) == 3
            assert all(step["status"] == "success" for step in results["steps"])
    
    def test_proposal_search_and_filtering(self, sample_api_client, mock_database):
        """Test proposal search and filtering capabilities."""
        # Create test proposals with different attributes
        proposals = [
            create_test_proposal(project_type="water_treatment", status="draft"),
            create_test_proposal(project_type="wastewater", status="submitted"),
            create_test_proposal(project_type="industrial", status="approved")
        ]
        
        with patch('services.proposal.router.ProposalService') as mock_service:
            # Test filtering by project type
            mock_service.return_value.list_proposals.return_value = {
                "proposals": [proposals[0]],
                "total": 1,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            response = sample_api_client.get("/proposal/proposals?project_type=water_treatment")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["proposals"]) == 1
            assert data["proposals"][0]["project_type"] == "water_treatment"
            
            # Test filtering by status
            mock_service.return_value.list_proposals.return_value = {
                "proposals": [proposals[1]],
                "total": 1,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            response = sample_api_client.get("/proposal/proposals?status=submitted")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["proposals"]) == 1
            assert data["proposals"][0]["status"] == "submitted"