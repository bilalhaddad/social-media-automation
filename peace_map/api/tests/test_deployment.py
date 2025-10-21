"""
Deployment tests for Peace Map API
"""

import pytest
import json
import os
import subprocess
import time
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


class TestDockerDeployment:
    """Test Docker deployment functionality"""
    
    def test_dockerfile_exists(self):
        """Test Dockerfile exists"""
        dockerfile_path = "peace_map/api/Dockerfile"
        assert os.path.exists(dockerfile_path)
        
        # Read Dockerfile content
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for essential Docker instructions
        assert "FROM python:3.11-slim" in content
        assert "WORKDIR /app" in content
        assert "COPY requirements.txt ." in content
        assert "RUN pip install" in content
        assert "EXPOSE 8000" in content
        assert "CMD" in content
    
    def test_docker_compose_exists(self):
        """Test docker-compose.yml exists"""
        compose_path = "peace_map/api/docker-compose.yml"
        assert os.path.exists(compose_path)
        
        # Read docker-compose.yml content
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check for essential services
        assert "api:" in content
        assert "db:" in content
        assert "redis:" in content
        assert "celery:" in content
        assert "celery-beat:" in content
    
    def test_docker_compose_services(self):
        """Test docker-compose services configuration"""
        compose_path = "peace_map/api/docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check API service
        assert "build: ." in content
        assert "ports:" in content
        assert "environment:" in content
        assert "depends_on:" in content
        assert "volumes:" in content
        assert "command:" in content
        
        # Check database service
        assert "image: postgres:15" in content
        assert "POSTGRES_DB=peace_map" in content
        assert "POSTGRES_USER=postgres" in content
        assert "POSTGRES_PASSWORD=password" in content
        
        # Check Redis service
        assert "image: redis:7-alpine" in content
        
        # Check Celery services
        assert "celery -A peace_map.api.celery worker" in content
        assert "celery -A peace_map.api.celery beat" in content
    
    def test_docker_health_check(self):
        """Test Docker health check configuration"""
        dockerfile_path = "peace_map/api/Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for health check
        assert "HEALTHCHECK" in content
        assert "curl -f http://localhost:8000/health" in content
        assert "interval=30s" in content
        assert "timeout=30s" in content
        assert "start-period=5s" in content
        assert "retries=3" in content
    
    def test_docker_security(self):
        """Test Docker security"""
        dockerfile_path = "peace_map/api/Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for security best practices
        assert "ENV PYTHONDONTWRITEBYTECODE=1" in content
        assert "ENV PYTHONUNBUFFERED=1" in content
        assert "RUN adduser --disabled-password" in content
        assert "USER appuser" in content
        
        # Check for non-root user
        assert "appuser" in content
    
    def test_docker_optimization(self):
        """Test Docker optimization"""
        dockerfile_path = "peace_map/api/Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for optimization practices
        assert "RUN apt-get update" in content
        assert "rm -rf /var/lib/apt/lists/*" in content
        assert "pip install --no-cache-dir" in content
        
        # Check for multi-stage build if applicable
        # (Not implemented in current Dockerfile, but could be added)
    
    def test_docker_environment_variables(self):
        """Test Docker environment variables"""
        compose_path = "peace_map/api/docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check for environment variables
        assert "DATABASE_URL=" in content
        assert "REDIS_URL=" in content
        assert "SECRET_KEY=" in content
        assert "DEBUG=" in content
        
        # Check for database environment
        assert "POSTGRES_DB=" in content
        assert "POSTGRES_USER=" in content
        assert "POSTGRES_PASSWORD=" in content


class TestEnvironmentConfiguration:
    """Test environment configuration"""
    
    def test_env_example_exists(self):
        """Test env.example exists"""
        env_path = "peace_map/api/env.example"
        assert os.path.exists(env_path)
        
        # Read env.example content
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for essential environment variables
        assert "DATABASE_URL=" in content
        assert "REDIS_URL=" in content
        assert "SECRET_KEY=" in content
        assert "DEBUG=" in content
        assert "HOST=" in content
        assert "PORT=" in content
    
    def test_env_variables_documented(self):
        """Test environment variables are documented"""
        env_path = "peace_map/api/env.example"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for documentation comments
        assert "# Database" in content
        assert "# Redis" in content
        assert "# Security" in content
        assert "# API Configuration" in content
        assert "# CORS" in content
        assert "# Rate Limiting" in content
        assert "# External Services" in content
        assert "# File Upload" in content
        assert "# Logging" in content
        assert "# Monitoring" in content
        assert "# Background Jobs" in content
        assert "# Email" in content
        assert "# SMS" in content
    
    def test_env_variables_validation(self):
        """Test environment variables validation"""
        env_path = "peace_map/api/env.example"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for required variables
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "DEBUG",
            "HOST",
            "PORT"
        ]
        
        for var in required_vars:
            assert f"{var}=" in content
    
    def test_env_variables_defaults(self):
        """Test environment variables have defaults"""
        env_path = "peace_map/api/env.example"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for default values
        assert "HOST=0.0.0.0" in content
        assert "PORT=8000" in content
        assert "DEBUG=true" in content
        assert "LOG_LEVEL=INFO" in content
        assert "RATE_LIMIT_CALLS_PER_MINUTE=60" in content


class TestProductionDeployment:
    """Test production deployment configuration"""
    
    def test_production_security(self):
        """Test production security configuration"""
        env_path = "peace_map/api/env.example"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for security settings
        assert "SECRET_KEY=" in content
        assert "DEBUG=false" in content
        assert "CORS" in content
        assert "Rate Limiting" in content
        assert "Security" in content
    
    def test_production_monitoring(self):
        """Test production monitoring configuration"""
        env_path = "peace_map/api/env.example"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for monitoring settings
        assert "Logging" in content
        assert "Monitoring" in content
        assert "Metrics" in content
        assert "Background Jobs" in content
    
    def test_production_scalability(self):
        """Test production scalability configuration"""
        compose_path = "peace_map/api/docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check for scalability features
        assert "celery:" in content
        assert "celery-beat:" in content
        assert "redis:" in content
        assert "db:" in content
        
        # Check for volume mounts
        assert "volumes:" in content
        assert "postgres_data:" in content
        assert "redis_data:" in content
    
    def test_production_health_checks(self):
        """Test production health checks"""
        compose_path = "peace_map/api/docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check for health check configuration
        # (Health checks are configured in Dockerfile, not docker-compose.yml)
        
        # Check for service dependencies
        assert "depends_on:" in content
        assert "db" in content
        assert "redis" in content
    
    def test_production_logging(self):
        """Test production logging configuration"""
        env_path = "peace_map/api/env.example"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for logging configuration
        assert "LOG_LEVEL=" in content
        assert "LOG_FORMAT=" in content
        
        # Check for structured logging
        assert "INFO" in content
        assert "asctime" in content
        assert "name" in content
        assert "levelname" in content
        assert "message" in content


class TestDeploymentScripts:
    """Test deployment scripts"""
    
    def test_deployment_scripts_exist(self):
        """Test deployment scripts exist"""
        # Check for common deployment script patterns
        # (These would be created as needed)
        
        # Check for requirements.txt
        requirements_path = "peace_map/api/requirements.txt"
        assert os.path.exists(requirements_path)
        
        # Check for README
        readme_path = "peace_map/api/README.md"
        assert os.path.exists(readme_path)
    
    def test_requirements_documented(self):
        """Test requirements are documented"""
        requirements_path = "peace_map/api/requirements.txt"
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        # Check for essential dependencies
        assert "fastapi" in content
        assert "uvicorn" in content
        assert "sqlalchemy" in content
        assert "pydantic" in content
        assert "python-jose" in content
        assert "passlib" in content
        assert "python-multipart" in content
        assert "httpx" in content
        assert "requests" in content
        assert "pandas" in content
        assert "numpy" in content
        assert "geopy" in content
        assert "folium" in content
        assert "scikit-learn" in content
        assert "transformers" in content
        assert "torch" in content
        assert "sentence-transformers" in content
        assert "faiss-cpu" in content
        assert "celery" in content
        assert "redis" in content
        assert "nltk" in content
        assert "spacy" in content
        assert "python-dotenv" in content
        assert "python-dateutil" in content
        assert "pytz" in content
        assert "pytest" in content
        assert "pytest-asyncio" in content
        assert "pytest-cov" in content
        assert "black" in content
        assert "flake8" in content
        assert "mypy" in content
    
    def test_readme_documented(self):
        """Test README is documented"""
        readme_path = "peace_map/api/README.md"
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for essential documentation sections
        assert "# Peace Map API" in content
        assert "## Features" in content
        assert "## Quick Start" in content
        assert "## Prerequisites" in content
        assert "## Installation" in content
        assert "## Docker" in content
        assert "## API Endpoints" in content
        assert "## Authentication" in content
        assert "## Rate Limiting" in content
        assert "## Error Handling" in content
        assert "## Development" in content
        assert "## Production Deployment" in content
        assert "## License" in content
    
    def test_readme_installation_instructions(self):
        """Test README installation instructions"""
        readme_path = "peace_map/api/README.md"
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for installation steps
        assert "Clone the repository" in content
        assert "Create virtual environment" in content
        assert "Install dependencies" in content
        assert "Set up environment variables" in content
        assert "Initialize database" in content
        assert "Run the application" in content
    
    def test_readme_docker_instructions(self):
        """Test README Docker instructions"""
        readme_path = "peace_map/api/README.md"
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for Docker instructions
        assert "Docker" in content
        assert "docker-compose" in content
        assert "Build and run" in content
        assert "Access the API" in content
        assert "localhost:8000" in content
        assert "docs" in content
        assert "health" in content
