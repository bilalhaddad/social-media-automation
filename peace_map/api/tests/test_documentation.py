"""
Documentation tests for Peace Map API
"""

import pytest
import json
from peace_map.api.models import db
from peace_map.api.app import app


@pytest.fixture
def client():
    """Test client fixture"""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


class TestAPIDocumentation:
    """Test API documentation functionality"""
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema generation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        
        # Check API info
        assert schema["info"]["title"] == "Peace Map API"
        assert schema["info"]["version"] == "1.0.0"
        assert "description" in schema["info"]
        
        # Check paths
        assert "/api/v1/suppliers" in schema["paths"]
        assert "/api/v1/projects/{project_id}/events" in schema["paths"]
        assert "/api/v1/risk-index" in schema["paths"]
        assert "/api/v1/alerts" in schema["paths"]
    
    def test_swagger_ui(self, client):
        """Test Swagger UI endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Should return HTML content
        assert "text/html" in response.content_type
        assert "swagger" in response.data.decode().lower()
    
    def test_redoc_ui(self, client):
        """Test ReDoc UI endpoint"""
        response = client.get("/redoc")
        assert response.status_code == 200
        
        # Should return HTML content
        assert "text/html" in response.content_type
        assert "redoc" in response.data.decode().lower()
    
    def test_api_endpoints_documented(self, client):
        """Test API endpoints are documented"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        paths = schema["paths"]
        
        # Check suppliers endpoints
        assert "/api/v1/suppliers" in paths
        assert "get" in paths["/api/v1/suppliers"]
        assert "post" in paths["/api/v1/suppliers"]
        
        assert "/api/v1/suppliers/{supplier_id}" in paths
        assert "get" in paths["/api/v1/suppliers/{supplier_id}"]
        assert "put" in paths["/api/v1/suppliers/{supplier_id}"]
        assert "delete" in paths["/api/v1/suppliers/{supplier_id}"]
        
        # Check events endpoints
        assert "/api/v1/projects/{project_id}/events" in paths
        assert "get" in paths["/api/v1/projects/{project_id}/events"]
        assert "post" in paths["/api/v1/projects/{project_id}/events"]
        
        assert "/api/v1/projects/{project_id}/events/{event_id}" in paths
        assert "get" in paths["/api/v1/projects/{project_id}/events/{event_id}"]
        assert "put" in paths["/api/v1/projects/{project_id}/events/{event_id}"]
        assert "delete" in paths["/api/v1/projects/{project_id}/events/{event_id}"]
        
        # Check risk index endpoints
        assert "/api/v1/risk-index" in paths
        assert "get" in paths["/api/v1/risk-index"]
        
        # Check alerts endpoints
        assert "/api/v1/alerts" in paths
        assert "get" in paths["/api/v1/alerts"]
        assert "post" in paths["/api/v1/alerts"]
        
        assert "/api/v1/alerts/{alert_id}" in paths
        assert "get" in paths["/api/v1/alerts/{alert_id}"]
        assert "put" in paths["/api/v1/alerts/{alert_id}"]
        assert "delete" in paths["/api/v1/alerts/{alert_id}"]
        
        assert "/api/v1/alerts/{alert_id}/acknowledge" in paths
        assert "post" in paths["/api/v1/alerts/{alert_id}/acknowledge"]
        
        assert "/api/v1/alerts/{alert_id}/resolve" in paths
        assert "post" in paths["/api/v1/alerts/{alert_id}/resolve"]
    
    def test_request_models_documented(self, client):
        """Test request models are documented"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check request models
        assert "EventCreate" in schemas
        assert "EventUpdate" in schemas
        assert "SupplierCreate" in schemas
        assert "SupplierUpdate" in schemas
        assert "AlertCreate" in schemas
        assert "AlertUpdate" in schemas
        
        # Check filter models
        assert "EventFilters" in schemas
        assert "SupplierFilters" in schemas
        assert "AlertFilters" in schemas
        assert "RiskIndexFilters" in schemas
        
        # Check pagination models
        assert "PaginationParams" in schemas
        assert "DateRangeParams" in schemas
    
    def test_response_models_documented(self, client):
        """Test response models are documented"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check response models
        assert "Event" in schemas
        assert "Supplier" in schemas
        assert "Alert" in schemas
        assert "RiskIndex" in schemas
        
        # Check enum models
        assert "EventType" in schemas
        assert "EventStatus" in schemas
        assert "RiskLevel" in schemas
        assert "AlertStatus" in schemas
    
    def test_authentication_documented(self, client):
        """Test authentication is documented"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        components = schema.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        # Check security schemes
        assert "BearerAuth" in security_schemes
        assert "ApiKeyAuth" in security_schemes
        
        # Check BearerAuth
        bearer_auth = security_schemes["BearerAuth"]
        assert bearer_auth["type"] == "http"
        assert bearer_auth["scheme"] == "bearer"
        assert "bearerFormat" in bearer_auth
        
        # Check ApiKeyAuth
        api_key_auth = security_schemes["ApiKeyAuth"]
        assert api_key_auth["type"] == "apiKey"
        assert api_key_auth["in"] == "header"
        assert api_key_auth["name"] == "X-API-Key"
    
    def test_security_requirements_documented(self, client):
        """Test security requirements are documented"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        security = schema.get("security", [])
        
        # Should have security requirements
        assert len(security) > 0
        
        # Check security requirements
        for requirement in security:
            assert "BearerAuth" in requirement or "ApiKeyAuth" in requirement
    
    def test_parameter_documentation(self, client):
        """Test parameter documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        paths = schema["paths"]
        
        # Check suppliers endpoint parameters
        suppliers_path = paths["/api/v1/suppliers"]
        get_operation = suppliers_path["get"]
        
        assert "parameters" in get_operation
        parameters = get_operation["parameters"]
        
        # Should have pagination parameters
        param_names = [param["name"] for param in parameters]
        assert "page" in param_names
        assert "size" in param_names
        
        # Should have filter parameters
        assert "name" in param_names
        assert "location" in param_names
        assert "risk_level" in param_names
    
    def test_response_documentation(self, client):
        """Test response documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        paths = schema["paths"]
        
        # Check suppliers endpoint responses
        suppliers_path = paths["/api/v1/suppliers"]
        get_operation = suppliers_path["get"]
        
        assert "responses" in get_operation
        responses = get_operation["responses"]
        
        # Should have success response
        assert "200" in responses
        success_response = responses["200"]
        assert "content" in success_response
        
        # Should have error responses
        assert "400" in responses
        assert "401" in responses
        assert "403" in responses
        assert "404" in responses
        assert "422" in responses
        assert "500" in responses
    
    def test_example_documentation(self, client):
        """Test example documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check example in EventCreate
        event_create = schemas.get("EventCreate", {})
        if "example" in event_create:
            example = event_create["example"]
            assert "title" in example
            assert "event_type" in example
            assert "location" in example
        
        # Check example in SupplierCreate
        supplier_create = schemas.get("SupplierCreate", {})
        if "example" in supplier_create:
            example = supplier_create["example"]
            assert "name" in example
            assert "location" in example
            assert "contact_email" in example
    
    def test_tag_documentation(self, client):
        """Test tag documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        tags = schema.get("tags", [])
        
        # Should have tags for different resource types
        tag_names = [tag["name"] for tag in tags]
        assert "Events" in tag_names or "events" in tag_names
        assert "Suppliers" in tag_names or "suppliers" in tag_names
        assert "Alerts" in tag_names or "alerts" in tag_names
        assert "Risk Index" in tag_names or "risk-index" in tag_names
    
    def test_operation_documentation(self, client):
        """Test operation documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        paths = schema["paths"]
        
        # Check suppliers endpoint operations
        suppliers_path = paths["/api/v1/suppliers"]
        
        # GET operation
        get_operation = suppliers_path["get"]
        assert "summary" in get_operation
        assert "description" in get_operation
        assert "tags" in get_operation
        
        # POST operation
        post_operation = suppliers_path["post"]
        assert "summary" in post_operation
        assert "description" in post_operation
        assert "tags" in post_operation
        
        # Should have request body
        assert "requestBody" in post_operation
        request_body = post_operation["requestBody"]
        assert "content" in request_body
        assert "application/json" in request_body["content"]
    
    def test_error_response_documentation(self, client):
        """Test error response documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = json.loads(response.data)
        paths = schema["paths"]
        
        # Check error responses
        suppliers_path = paths["/api/v1/suppliers"]
        get_operation = suppliers_path["get"]
        responses = get_operation["responses"]
        
        # 400 Bad Request
        if "400" in responses:
            bad_request = responses["400"]
            assert "description" in bad_request
            assert "content" in bad_request
        
        # 401 Unauthorized
        if "401" in responses:
            unauthorized = responses["401"]
            assert "description" in unauthorized
            assert "content" in unauthorized
        
        # 403 Forbidden
        if "403" in responses:
            forbidden = responses["403"]
            assert "description" in forbidden
            assert "content" in forbidden
        
        # 404 Not Found
        if "404" in responses:
            not_found = responses["404"]
            assert "description" in not_found
            assert "content" in not_found
        
        # 422 Validation Error
        if "422" in responses:
            validation_error = responses["422"]
            assert "description" in validation_error
            assert "content" in validation_error
        
        # 500 Internal Server Error
        if "500" in responses:
            internal_error = responses["500"]
            assert "description" in internal_error
            assert "content" in internal_error
