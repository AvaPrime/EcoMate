"""Integration tests for the Catalog Service.

These tests verify the catalog service API endpoints work correctly
with realistic product data and proper error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from tests.test_utils import APITestHelper, IntegrationHelper
from tests.factories import create_test_product, create_realistic_pump_catalog, create_realistic_uv_catalog


class TestCatalogServiceIntegration:
    """Integration tests for catalog service endpoints."""
    
    def test_catalog_service_health(self, sample_api_client):
        """Test catalog service health endpoint."""
        response = sample_api_client.get("/catalog/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "ok"
        assert "timestamp" in health_data
        assert "service" in health_data
        assert health_data["service"] == "catalog"
    
    def test_get_products_success(self, sample_api_client, mock_database):
        """Test successful product listing."""
        # Create test products
        products = [
            create_test_product(product_type="pump", name="Centrifugal Pump CP-100"),
            create_test_product(product_type="uv_reactor", name="UV Sterilizer UV-200"),
            create_test_product(product_type="filter", name="Sand Filter SF-300")
        ]
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_products.return_value = {
                "products": products,
                "total": 3,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            response = sample_api_client.get("/catalog/products")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["products"]) == 3
            assert data["total"] == 3
            assert "page" in data
            assert "per_page" in data
    
    def test_get_product_by_id_success(self, sample_api_client, mock_database):
        """Test successful product retrieval by ID."""
        product = create_test_product(
            product_type="pump",
            name="High-Efficiency Pump HE-500",
            specifications={
                "flow_rate_lpm": 500,
                "head_pressure_m": 50,
                "power_consumption_kw": 5.5
            }
        )
        product_id = product["id"]
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_product.return_value = product
            
            response = sample_api_client.get(f"/catalog/products/{product_id}")
            
            assert response.status_code == 200
            retrieved_product = response.json()
            
            assert retrieved_product["id"] == product_id
            assert retrieved_product["name"] == "High-Efficiency Pump HE-500"
            assert retrieved_product["product_type"] == "pump"
            assert "specifications" in retrieved_product
    
    def test_get_product_not_found(self, sample_api_client, mock_database):
        """Test product retrieval with non-existent ID."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_product.return_value = None
            
            response = sample_api_client.get(f"/catalog/products/{non_existent_id}")
            
            assert response.status_code == 404
            error_data = response.json()
            assert "detail" in error_data
            assert "not found" in error_data["detail"].lower()
    
    def test_search_products_by_type(self, sample_api_client, mock_database):
        """Test product search by type."""
        pump_products = create_realistic_pump_catalog(count=5)
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.search_products.return_value = {
                "products": pump_products,
                "total": 5,
                "page": 1,
                "per_page": 10,
                "pages": 1,
                "filters_applied": {"product_type": "pump"}
            }
            
            response = sample_api_client.get("/catalog/products/search?product_type=pump")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["products"]) == 5
            assert all(product["product_type"] == "pump" for product in data["products"])
            assert data["filters_applied"]["product_type"] == "pump"
    
    def test_search_products_by_specifications(self, sample_api_client, mock_database):
        """Test product search by specifications."""
        matching_products = [
            create_test_product(
                product_type="pump",
                specifications={"flow_rate_lpm": 1000, "head_pressure_m": 30}
            ),
            create_test_product(
                product_type="pump",
                specifications={"flow_rate_lpm": 1200, "head_pressure_m": 35}
            )
        ]
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.search_products.return_value = {
                "products": matching_products,
                "total": 2,
                "page": 1,
                "per_page": 10,
                "pages": 1,
                "filters_applied": {
                    "min_flow_rate": 1000,
                    "min_head_pressure": 30
                }
            }
            
            response = sample_api_client.get(
                "/catalog/products/search?min_flow_rate=1000&min_head_pressure=30"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["products"]) == 2
            for product in data["products"]:
                specs = product["specifications"]
                assert specs["flow_rate_lpm"] >= 1000
                assert specs["head_pressure_m"] >= 30
    
    def test_get_product_categories(self, sample_api_client, mock_database):
        """Test product categories endpoint."""
        categories = {
            "pump": {
                "name": "Pumps",
                "description": "Water pumping equipment",
                "count": 25,
                "subcategories": ["centrifugal", "submersible", "booster"]
            },
            "uv_reactor": {
                "name": "UV Reactors",
                "description": "UV disinfection systems",
                "count": 15,
                "subcategories": ["low_pressure", "medium_pressure", "amalgam"]
            },
            "filter": {
                "name": "Filters",
                "description": "Water filtration systems",
                "count": 30,
                "subcategories": ["sand", "carbon", "membrane"]
            }
        }
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_categories.return_value = categories
            
            response = sample_api_client.get("/catalog/categories")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "pump" in data
            assert "uv_reactor" in data
            assert "filter" in data
            
            assert data["pump"]["count"] == 25
            assert len(data["pump"]["subcategories"]) == 3
    
    def test_get_product_specifications_schema(self, sample_api_client):
        """Test product specifications schema endpoint."""
        schema = {
            "pump": {
                "flow_rate_lpm": {"type": "number", "unit": "L/min", "required": True},
                "head_pressure_m": {"type": "number", "unit": "m", "required": True},
                "power_consumption_kw": {"type": "number", "unit": "kW", "required": True},
                "material": {"type": "string", "enum": ["stainless_steel", "cast_iron", "bronze"]},
                "inlet_size_mm": {"type": "number", "unit": "mm"},
                "outlet_size_mm": {"type": "number", "unit": "mm"}
            },
            "uv_reactor": {
                "flow_rate_lpm": {"type": "number", "unit": "L/min", "required": True},
                "uv_dose_mj_cm2": {"type": "number", "unit": "mJ/cm²", "required": True},
                "lamp_power_w": {"type": "number", "unit": "W", "required": True},
                "lamp_type": {"type": "string", "enum": ["low_pressure", "medium_pressure", "amalgam"]},
                "chamber_material": {"type": "string", "enum": ["stainless_steel", "pvc"]}
            }
        }
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_specifications_schema.return_value = schema
            
            response = sample_api_client.get("/catalog/specifications/schema")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "pump" in data
            assert "uv_reactor" in data
            
            pump_schema = data["pump"]
            assert "flow_rate_lpm" in pump_schema
            assert pump_schema["flow_rate_lpm"]["required"] is True
            assert pump_schema["flow_rate_lpm"]["unit"] == "L/min"
    
    def test_compare_products(self, sample_api_client, mock_database):
        """Test product comparison endpoint."""
        product1 = create_test_product(
            product_type="pump",
            name="Pump A",
            specifications={"flow_rate_lpm": 1000, "power_consumption_kw": 5.0}
        )
        product2 = create_test_product(
            product_type="pump",
            name="Pump B",
            specifications={"flow_rate_lpm": 1200, "power_consumption_kw": 6.0}
        )
        
        comparison_result = {
            "products": [product1, product2],
            "comparison": {
                "flow_rate_lpm": {
                    "product1": 1000,
                    "product2": 1200,
                    "winner": "product2"
                },
                "power_consumption_kw": {
                    "product1": 5.0,
                    "product2": 6.0,
                    "winner": "product1"  # Lower is better for power consumption
                }
            },
            "overall_score": {
                "product1": 7.5,
                "product2": 8.2
            }
        }
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.compare_products.return_value = comparison_result
            
            response = sample_api_client.post(
                "/catalog/products/compare",
                json={"product_ids": [product1["id"], product2["id"]]}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["products"]) == 2
            assert "comparison" in data
            assert "overall_score" in data
            assert data["comparison"]["flow_rate_lpm"]["winner"] == "product2"
    
    def test_get_product_recommendations(self, sample_api_client, mock_database, mock_external_apis):
        """Test product recommendations endpoint."""
        requirements = {
            "project_type": "water_treatment",
            "flow_rate_lpm": 800,
            "budget_usd": 25000,
            "treatment_goals": ["disinfection", "filtration"]
        }
        
        recommendations = {
            "recommended_products": [
                {
                    "product": create_test_product(product_type="pump"),
                    "match_score": 0.95,
                    "reasons": ["Flow rate matches requirements", "Within budget"]
                },
                {
                    "product": create_test_product(product_type="uv_reactor"),
                    "match_score": 0.88,
                    "reasons": ["Excellent for disinfection", "Energy efficient"]
                }
            ],
            "total_estimated_cost": 22000,
            "confidence_score": 0.92
        }
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_recommendations.return_value = recommendations
            
            response = sample_api_client.post("/catalog/recommendations", json=requirements)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["recommended_products"]) == 2
            assert data["total_estimated_cost"] == 22000
            assert data["confidence_score"] == 0.92
            
            for rec in data["recommended_products"]:
                assert "product" in rec
                assert "match_score" in rec
                assert "reasons" in rec
                assert rec["match_score"] > 0.8
    
    def test_catalog_bulk_operations(self, sample_api_client, mock_database):
        """Test bulk catalog operations."""
        product_ids = ["prod-1", "prod-2", "prod-3"]
        products = [create_test_product() for _ in range(3)]
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.get_products_bulk.return_value = {
                "products": products,
                "found_count": 3,
                "not_found_ids": []
            }
            
            response = sample_api_client.post(
                "/catalog/products/bulk",
                json={"product_ids": product_ids}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["products"]) == 3
            assert data["found_count"] == 3
            assert len(data["not_found_ids"]) == 0
    
    def test_catalog_search_validation(self, sample_api_client):
        """Test catalog search parameter validation."""
        # Test invalid search parameters
        response = sample_api_client.get("/catalog/products/search?min_flow_rate=-100")
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        
        # Check validation error for negative flow rate
        errors = error_data["detail"]
        assert any("min_flow_rate" in str(error) for error in errors)
    
    @pytest.mark.slow
    def test_catalog_integration_flow(self, sample_api_client, mock_database, mock_external_apis):
        """Test complete catalog workflow integration."""
        integration_helper = IntegrationTestHelper(sample_api_client)
        
        flow_config = {
            "steps": [
                {
                    "name": "Check service health",
                    "method": "GET",
                    "endpoint": "/catalog/health",
                    "expected_status": 200
                },
                {
                    "name": "Get product categories",
                    "method": "GET",
                    "endpoint": "/catalog/categories",
                    "expected_status": 200
                },
                {
                    "name": "Search for pumps",
                    "method": "GET",
                    "endpoint": "/catalog/products/search?product_type=pump",
                    "expected_status": 200
                },
                {
                    "name": "Get product recommendations",
                    "method": "POST",
                    "endpoint": "/catalog/recommendations",
                    "data": {
                        "project_type": "water_treatment",
                        "flow_rate_lpm": 500,
                        "budget_usd": 30000
                    },
                    "expected_status": 200
                }
            ]
        }
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            # Mock all service methods
            mock_service.return_value.get_categories.return_value = {"pump": {"count": 10}}
            mock_service.return_value.search_products.return_value = {
                "products": create_realistic_pump_catalog(count=3),
                "total": 3
            }
            mock_service.return_value.get_recommendations.return_value = {
                "recommended_products": [
                    {"product": create_test_product(), "match_score": 0.9, "reasons": []}
                ],
                "confidence_score": 0.85
            }
            
            results = integration_helper.test_service_integration_flow(flow_config)
            
            assert results["overall_status"] == "success"
            assert len(results["steps"]) == 4
            assert all(step["status"] == "success" for step in results["steps"])
    
    def test_catalog_performance_search(self, sample_api_client, mock_database):
        """Test catalog search performance with large datasets."""
        # Simulate large catalog search
        large_catalog = create_realistic_pump_catalog(count=100)
        
        with patch('services.catalog.router.CatalogService') as mock_service:
            mock_service.return_value.search_products.return_value = {
                "products": large_catalog[:10],  # First page
                "total": 100,
                "page": 1,
                "per_page": 10,
                "pages": 10,
                "search_time_ms": 45
            }
            
            response = sample_api_client.get("/catalog/products/search?per_page=10")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["products"]) == 10
            assert data["total"] == 100
            assert data["pages"] == 10
            assert "search_time_ms" in data
            assert data["search_time_ms"] < 100  # Performance threshold