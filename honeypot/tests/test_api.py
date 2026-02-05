import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)

# Mock API key for testing
TEST_API_KEY = "test-key-change-in-production"


def test_health_check():
    """Test health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_missing_api_key():
    """Test 401 when API key is missing"""
    response = client.post("/api/v1/honeypot", json={"message": "test"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_MISSING"


def test_invalid_api_key():
    """Test 403 when API key is invalid"""
    response = client.post(
        "/api/v1/honeypot", headers={"X-API-Key": "wrong-key"}, json={"message": "test"}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_INVALID"


def test_digital_arrest_scam():
    """Test digital arrest scam detection"""
    response = client.post(
        "/api/v1/honeypot",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "message": "This is Inspector Raj from CBI. Your Aadhaar is linked to fraud. Transfer Rs 50000 to account 123456789012 IFSC SBIN0001234 or face arrest."
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "scam_detection" in data
    assert "extracted_intelligence" in data


def test_extraction_bank_account():
    """Test bank account extraction"""
    from app.extraction import ExtractionEngine

    engine = ExtractionEngine()
    text = "Send money to account 1234567890123456"
    accounts = engine.extract_bank_accounts(text)

    assert len(accounts) == 1
    assert accounts[0].account_number == "1234567890123456"


def test_extraction_upi():
    """Test UPI ID extraction"""
    from app.extraction import ExtractionEngine

    engine = ExtractionEngine()
    text = "My UPI is fraudster@ybl"
    upis = engine.extract_upi_ids(text)

    assert len(upis) == 1
    assert upis[0].upi_id == "fraudster@ybl"


def test_extraction_phone():
    """Test phone number extraction"""
    from app.extraction import ExtractionEngine

    engine = ExtractionEngine()
    text = "Call me on +919876543210"
    phones = engine.extract_phone_numbers(text)

    assert len(phones) == 1
    assert "9876543210" in phones[0].number


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
