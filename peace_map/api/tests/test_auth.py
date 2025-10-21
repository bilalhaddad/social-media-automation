"""
Tests for Peace Map API authentication
"""

import pytest
from datetime import datetime, timedelta
from peace_map.api.models import db
from peace_map.api.app import app
from peace_map.api.auth import auth_manager


@pytest.fixture
def client():
    """Test client fixture"""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


class TestAuthentication:
    """Test authentication functionality"""
    
    def test_create_access_token(self, client):
        """Test creating access token"""
        data = {"user_id": 1, "role": "admin"}
        token = auth_manager.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self, client):
        """Test verifying token"""
        data = {"user_id": 1, "role": "admin"}
        token = auth_manager.create_access_token(data)
        
        payload = auth_manager.verify_token(token)
        
        assert payload["user_id"] == 1
        assert payload["role"] == "admin"
    
    def test_verify_invalid_token(self, client):
        """Test verifying invalid token"""
        with pytest.raises(Exception):
            auth_manager.verify_token("invalid-token")
    
    def test_token_expiration(self, client):
        """Test token expiration"""
        data = {"user_id": 1, "role": "admin"}
        expires_delta = timedelta(seconds=1)
        token = auth_manager.create_access_token(data, expires_delta)
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        with pytest.raises(Exception):
            auth_manager.verify_token(token)
    
    def test_password_hashing(self, client):
        """Test password hashing"""
        password = "test-password"
        hashed = auth_manager.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        
        # Verify password
        assert auth_manager.verify_password(password, hashed) is True
        assert auth_manager.verify_password("wrong-password", hashed) is False


class TestAuthorization:
    """Test authorization functionality"""
    
    def test_require_auth_success(self, client):
        """Test successful authentication"""
        data = {"user_id": 1, "role": "admin"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/suppliers", headers=headers)
        
        # Should not return 401 (unauthorized)
        assert response.status_code != 401
    
    def test_require_auth_failure(self, client):
        """Test failed authentication"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/suppliers", headers=headers)
        
        # Should return 401 (unauthorized)
        assert response.status_code == 401
    
    def test_require_auth_no_token(self, client):
        """Test authentication without token"""
        response = client.get("/api/v1/suppliers")
        
        # Should return 401 (unauthorized)
        assert response.status_code == 401
    
    def test_require_admin_success(self, client):
        """Test successful admin authorization"""
        data = {"user_id": 1, "role": "admin"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/suppliers", headers=headers)
        
        # Should not return 403 (forbidden)
        assert response.status_code != 403
    
    def test_require_admin_failure(self, client):
        """Test failed admin authorization"""
        data = {"user_id": 1, "role": "viewer"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/suppliers", headers=headers)
        
        # Should not return 403 (forbidden) for read operations
        assert response.status_code != 403
    
    def test_require_write_permission_success(self, client):
        """Test successful write permission"""
        data = {"user_id": 1, "role": "editor"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/v1/suppliers",
            data='{"name": "Test Supplier", "location": "Test Location"}',
            headers=headers
        )
        
        # Should not return 403 (forbidden)
        assert response.status_code != 403
    
    def test_require_write_permission_failure(self, client):
        """Test failed write permission"""
        data = {"user_id": 1, "role": "viewer"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/v1/suppliers",
            data='{"name": "Test Supplier", "location": "Test Location"}',
            headers=headers
        )
        
        # Should return 403 (forbidden)
        assert response.status_code == 403
    
    def test_require_read_permission_success(self, client):
        """Test successful read permission"""
        data = {"user_id": 1, "role": "viewer"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/suppliers", headers=headers)
        
        # Should not return 403 (forbidden)
        assert response.status_code != 403
    
    def test_require_read_permission_failure(self, client):
        """Test failed read permission"""
        data = {"user_id": 1, "role": "guest"}
        token = auth_manager.create_access_token(data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/suppliers", headers=headers)
        
        # Should return 403 (forbidden)
        assert response.status_code == 403


class TestPermissionChecker:
    """Test permission checker functionality"""
    
    def test_can_read(self, client):
        """Test read permission check"""
        from peace_map.api.auth import PermissionChecker
        
        # Admin can read everything
        admin_user = {"role": "admin"}
        admin_checker = PermissionChecker(admin_user)
        assert admin_checker.can_read("events") is True
        assert admin_checker.can_read("suppliers") is True
        
        # User with specific permissions
        user_with_permissions = {
            "role": "user",
            "permissions": ["read:events", "read:suppliers"]
        }
        user_checker = PermissionChecker(user_with_permissions)
        assert user_checker.can_read("events") is True
        assert user_checker.can_read("suppliers") is True
        assert user_checker.can_read("alerts") is False
    
    def test_can_write(self, client):
        """Test write permission check"""
        from peace_map.api.auth import PermissionChecker
        
        # Admin can write everything
        admin_user = {"role": "admin"}
        admin_checker = PermissionChecker(admin_user)
        assert admin_checker.can_write("events") is True
        assert admin_checker.can_write("suppliers") is True
        
        # User with specific permissions
        user_with_permissions = {
            "role": "user",
            "permissions": ["write:events"]
        }
        user_checker = PermissionChecker(user_with_permissions)
        assert user_checker.can_write("events") is True
        assert user_checker.can_write("suppliers") is False
    
    def test_can_delete(self, client):
        """Test delete permission check"""
        from peace_map.api.auth import PermissionChecker
        
        # Admin can delete everything
        admin_user = {"role": "admin"}
        admin_checker = PermissionChecker(admin_user)
        assert admin_checker.can_delete("events") is True
        assert admin_checker.can_delete("suppliers") is True
        
        # User with specific permissions
        user_with_permissions = {
            "role": "user",
            "permissions": ["delete:events"]
        }
        user_checker = PermissionChecker(user_with_permissions)
        assert user_checker.can_delete("events") is True
        assert user_checker.can_delete("suppliers") is False
    
    def test_can_manage_users(self, client):
        """Test user management permission check"""
        from peace_map.api.auth import PermissionChecker
        
        # Admin can manage users
        admin_user = {"role": "admin"}
        admin_checker = PermissionChecker(admin_user)
        assert admin_checker.can_manage_users() is True
        
        # Regular user cannot manage users
        regular_user = {"role": "user"}
        regular_checker = PermissionChecker(regular_user)
        assert regular_checker.can_manage_users() is False
    
    def test_can_manage_system(self, client):
        """Test system management permission check"""
        from peace_map.api.auth import PermissionChecker
        
        # Admin can manage system
        admin_user = {"role": "admin"}
        admin_checker = PermissionChecker(admin_user)
        assert admin_checker.can_manage_system() is True
        
        # Regular user cannot manage system
        regular_user = {"role": "user"}
        regular_checker = PermissionChecker(regular_user)
        assert regular_checker.can_manage_system() is False
