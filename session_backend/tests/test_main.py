"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestMainApplication:
    """Tests for the main FastAPI application."""
    
    def test_health_endpoint(self):
        """Test the basic health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "session-backend-api"
    
    def test_app_creation(self):
        """Test that the FastAPI app is created successfully."""
        assert app is not None
        assert app.title == "Session Backend API"
        assert app.description == "FastAPI backend for Strands session persistence"
        assert app.version == "0.1.0"