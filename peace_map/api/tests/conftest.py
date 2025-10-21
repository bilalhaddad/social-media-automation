"""
Test configuration for Peace Map API
"""

import pytest
from fastapi.testclient import TestClient
from peace_map.api.app import app
from peace_map.api.models import db


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def auth_headers():
    """Authentication headers fixture"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_event_data():
    """Sample event data fixture"""
    return {
        "title": "Test Event",
        "description": "Test Description",
        "event_type": "protest",
        "location": "Test Location",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "source": "Test Source",
        "source_confidence": 0.8,
        "published_at": "2024-01-01T00:00:00Z",
        "tags": ["test", "event"]
    }


@pytest.fixture
def sample_supplier_data():
    """Sample supplier data fixture"""
    return {
        "name": "Test Supplier",
        "location": "Test Location",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "contact_email": "test@example.com",
        "contact_phone": "+1234567890",
        "website": "https://example.com",
        "description": "Test Supplier Description",
        "tags": ["test", "supplier"]
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data fixture"""
    return {
        "supplier_id": 1,
        "risk_threshold": 75.0,
        "notification_email": "alert@example.com",
        "notification_phone": "+1234567890",
        "description": "Test Alert",
        "tags": ["test", "alert"]
    }
