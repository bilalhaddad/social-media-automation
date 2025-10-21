"""
Authentication and authorization for Peace Map API
"""

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-here"  # Should be in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key")


class AuthManager:
    """Authentication manager"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from token"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    # In a real application, you would validate the user exists in the database
    # For now, we'll just return the payload
    return payload


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from token (optional)"""
    try:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        payload = auth_manager.verify_token(token)
        return payload
    except Exception:
        return None


async def get_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Get API key from header"""
    # In a real application, you would validate the API key against a database
    # For now, we'll just return the key
    return api_key


def require_auth(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require authentication"""
    return user


def require_api_key(api_key: str = Depends(get_api_key)) -> str:
    """Require API key"""
    return api_key


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin privileges"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return user


def require_write_permission(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require write permission"""
    if user.get("role") not in ["admin", "editor"]:
        raise HTTPException(
            status_code=403,
            detail="Write permission required"
        )
    return user


def require_read_permission(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require read permission"""
    if user.get("role") not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="Read permission required"
        )
    return user


class PermissionChecker:
    """Permission checker for fine-grained access control"""
    
    def __init__(self, user: Dict[str, Any]):
        self.user = user
        self.role = user.get("role", "viewer")
        self.permissions = user.get("permissions", [])
    
    def can_read(self, resource: str) -> bool:
        """Check if user can read resource"""
        if self.role == "admin":
            return True
        return f"read:{resource}" in self.permissions
    
    def can_write(self, resource: str) -> bool:
        """Check if user can write resource"""
        if self.role == "admin":
            return True
        return f"write:{resource}" in self.permissions
    
    def can_delete(self, resource: str) -> bool:
        """Check if user can delete resource"""
        if self.role == "admin":
            return True
        return f"delete:{resource}" in self.permissions
    
    def can_manage_users(self) -> bool:
        """Check if user can manage users"""
        return self.role == "admin"
    
    def can_manage_system(self) -> bool:
        """Check if user can manage system"""
        return self.role == "admin"


def get_permission_checker(user: Dict[str, Any] = Depends(get_current_user)) -> PermissionChecker:
    """Get permission checker for current user"""
    return PermissionChecker(user)
