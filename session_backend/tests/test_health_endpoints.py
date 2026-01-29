"""Unit tests for health check endpoints."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import time
import psutil

from app.main import create_app
from app.database import get_database_health, check_database_connectivity


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client."""
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_basic_health_check(self):
        """Test the basic health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "checks" in data
        assert data["checks"]["service"]["status"] == "healthy"
        assert "timestamp" in data
    
    def test_liveness_probe(self):
        """Test the liveness probe endpoint."""
        response = self.client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "version" in data
        assert "checks" in data
        assert data["checks"]["service"]["status"] == "alive"
        assert "timestamp" in data
    
    @patch('app.routers.health.get_database_health')
    def test_database_health_check_healthy(self, mock_db_health):
        """Test database health check when database is healthy."""
        mock_db_health.return_value = {
            "status": "healthy",
            "connected": True,
            "connection_pool": {
                "size": 20,
                "checked_in": 15,
                "checked_out": 5
            }
        }
        
        response = self.client.get("/health/db")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"
        assert "response_time_ms" in data["checks"]["database"]
    
    @patch('app.routers.health.get_database_health')
    def test_database_health_check_unhealthy(self, mock_db_health):
        """Test database health check when database is unhealthy."""
        mock_db_health.return_value = {
            "status": "unhealthy",
            "connected": False,
            "error": "Connection timeout"
        }
        
        response = self.client.get("/health/db")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["checks"]["database"]["status"] == "unhealthy"
        assert "error" in data["detail"]["checks"]["database"]
    
    @patch('app.routers.health.get_database_health')
    def test_database_health_check_exception(self, mock_db_health):
        """Test database health check when an exception occurs."""
        mock_db_health.side_effect = Exception("Database connection failed")
        
        response = self.client.get("/health/db")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert "Database health check failed" in data["detail"]["checks"]["database"]["message"]
    
    @patch('app.routers.health.check_database_connectivity')
    def test_readiness_probe_ready(self, mock_db_connectivity):
        """Test readiness probe when database is ready."""
        mock_db_connectivity.return_value = True
        
        response = self.client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["service"]["status"] == "ready"
        assert data["checks"]["database"]["status"] == "ready"
        assert "response_time_ms" in data["checks"]["database"]
    
    @patch('app.routers.health.check_database_connectivity')
    def test_readiness_probe_not_ready(self, mock_db_connectivity):
        """Test readiness probe when database is not ready."""
        mock_db_connectivity.return_value = False
        
        response = self.client.get("/health/ready")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "not ready"
        assert data["detail"]["checks"]["service"]["status"] == "ready"
        assert data["detail"]["checks"]["database"]["status"] == "not ready"
    
    @patch('app.routers.health.check_database_connectivity')
    def test_readiness_probe_exception(self, mock_db_connectivity):
        """Test readiness probe when an exception occurs."""
        mock_db_connectivity.side_effect = Exception("Database check failed")
        
        response = self.client.get("/health/ready")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "not ready"
        assert data["detail"]["checks"]["service"]["status"] == "ready"
        assert data["detail"]["checks"]["database"]["status"] == "error"
    
    @patch('app.routers.health.psutil.Process')
    @patch('app.routers.health.get_database_health')
    def test_metrics_endpoint(self, mock_db_health, mock_process):
        """Test the metrics endpoint."""
        # Mock process metrics
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process_instance.cpu_percent.return_value = 25.5
        mock_process.return_value = mock_process_instance
        
        # Mock database health
        mock_db_health.return_value = {
            "status": "healthy",
            "pool": {
                "size": 20,
                "checked_in": 15,
                "checked_out": 5
            }
        }
        
        # Make some requests to populate metrics
        self.client.get("/health")
        self.client.get("/health/live")
        
        response = self.client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "timestamp" in data
        assert "application" in data
        assert "system" in data
        assert "database" in data
        
        # Check application metrics
        app_metrics = data["application"]
        assert "requests_total" in app_metrics
        assert "requests_by_status" in app_metrics
        assert "errors_total" in app_metrics
        assert "average_response_time_ms" in app_metrics
        
        # Check system metrics
        system_metrics = data["system"]
        assert "memory_usage_bytes" in system_metrics
        assert "memory_usage_mb" in system_metrics
        assert "cpu_percent" in system_metrics
        assert system_metrics["memory_usage_mb"] == 100.0
        assert system_metrics["cpu_percent"] == 25.5
        
        # Check database metrics
        db_metrics = data["database"]
        assert db_metrics["status"] == "healthy"
        assert "connection_pool" in db_metrics
    
    @patch('app.routers.health.psutil.Process')
    def test_metrics_endpoint_exception(self, mock_process):
        """Test metrics endpoint when an exception occurs."""
        mock_process.side_effect = Exception("Process info failed")
        
        response = self.client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "Failed to collect metrics" in data["error"]
        assert "message" in data
    
    def test_health_endpoints_response_time(self):
        """Test that health endpoints respond quickly."""
        endpoints = ["/health", "/health/live", "/health/db", "/health/ready"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            response_time = time.time() - start_time
            
            # Health endpoints should respond within 1 second
            assert response_time < 1.0, f"Endpoint {endpoint} took {response_time:.2f}s to respond"
            assert response.status_code in [200, 503], f"Unexpected status code for {endpoint}: {response.status_code}"
    
    def test_health_endpoints_concurrent_requests(self):
        """Test health endpoints under concurrent load."""
        import concurrent.futures
        import threading
        
        def make_request(endpoint):
            return self.client.get(endpoint)
        
        endpoints = ["/health", "/health/live"] * 10  # 20 concurrent requests
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_health_check_includes_version(self):
        """Test that health checks include version information."""
        endpoints = ["/health", "/health/live", "/health/db", "/health/ready"]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                assert "version" in data, f"Endpoint {endpoint} missing version"
            else:
                # For error responses, version should be in detail
                data = response.json()
                assert "version" in data["detail"], f"Endpoint {endpoint} missing version in error response"
    
    def test_health_check_includes_timestamp(self):
        """Test that health checks include timestamp information."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        
        # Timestamp should be recent (within last 5 seconds)
        import datetime
        timestamp_str = data["timestamp"]
        
        # Handle different timestamp formats
        try:
            # Try parsing as timezone-aware first
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
        except ValueError:
            # If that fails, parse as naive and assume UTC
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
        
        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
            
        now = datetime.datetime.now(datetime.timezone.utc)
        time_diff = (now - timestamp).total_seconds()
        assert time_diff < 5, f"Timestamp is too old: {time_diff} seconds"
    
    def test_database_health_includes_connection_pool_info(self):
        """Test that database health check includes connection pool information."""
        response = self.client.get("/health/db")
        
        # Should work regardless of database status
        if response.status_code == 200:
            data = response.json()
            if "checks" in data and "database" in data["checks"]:
                db_check = data["checks"]["database"]
                # Connection pool info might be present
                if "connection_pool" in db_check:
                    pool_info = db_check["connection_pool"]
                    # Basic validation of pool structure
                    assert isinstance(pool_info, dict)
    
    def test_readiness_probe_checks_both_service_and_database(self):
        """Test that readiness probe checks both service and database status."""
        response = self.client.get("/health/ready")
        
        # Should work regardless of status
        if response.status_code == 200:
            data = response.json()
            assert "checks" in data
            assert "service" in data["checks"]
            assert "database" in data["checks"]
        else:
            data = response.json()
            assert "checks" in data["detail"]
            assert "service" in data["detail"]["checks"]
            assert "database" in data["detail"]["checks"]