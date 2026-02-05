"""
Comprehensive validation tests for the honeypot API.
Tests all critical paths to ensure JSON schema consistency.
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.schemas import HoneypotResponse

client = TestClient(app)

# Test API key
TEST_API_KEY = "test-key-change-in-production"

# Set test environment
os.environ["API_KEY"] = TEST_API_KEY
os.environ["DISABLE_DELAYS"] = "1"  # Disable delays for fast tests


class TestSchemaConsistency:
    """Test that all response paths return consistent JSON structure."""

    def _validate_response_structure(self, response_data):
        """Validate that response matches expected schema."""
        required_top_level = [
            "session_id",
            "timestamp",
            "scam_detection",
            "honeypot_response",
            "extracted_intelligence",
            "engagement_metrics",
            "conversation_state",
        ]

        # Check all top-level fields present
        for field in required_top_level:
            assert field in response_data, f"Missing top-level field: {field}"

        # Validate scam_detection structure
        scam_detection = response_data["scam_detection"]
        assert "is_scam" in scam_detection
        assert "confidence" in scam_detection
        assert "scam_type" in scam_detection
        assert "threat_level" in scam_detection
        assert "reasoning" in scam_detection

        # Validate honeypot_response structure
        honeypot_response = response_data["honeypot_response"]
        assert "message" in honeypot_response
        assert "persona_used" in honeypot_response
        assert "strategy" in honeypot_response

        # Validate extracted_intelligence structure
        intel = response_data["extracted_intelligence"]
        assert "bank_accounts" in intel
        assert "upi_ids" in intel
        assert "phone_numbers" in intel
        assert "urls" in intel
        assert "emails" in intel
        assert "scammer_identity" in intel

        # Validate engagement_metrics structure
        metrics = response_data["engagement_metrics"]
        assert "turn_number" in metrics
        assert "total_turns" in metrics
        assert "response_time_ms" in metrics

        # Validate conversation_state structure
        state = response_data["conversation_state"]
        assert "status" in state
        assert "intel_collected" in state
        assert "intel_pending" in state

        # Type checks
        assert isinstance(response_data["session_id"], str)
        assert isinstance(scam_detection["is_scam"], bool)
        assert isinstance(scam_detection["confidence"], (int, float))
        assert isinstance(intel["bank_accounts"], list)
        assert isinstance(intel["upi_ids"], list)
        assert isinstance(intel["phone_numbers"], list)


class TestAuthentication:
    """Test authentication and authorization."""

    def test_health_no_auth_required(self):
        """Health endpoint should not require auth."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_missing_api_key_returns_401(self):
        """Missing API key should return 401."""
        response = client.post("/api/v1/honeypot", json={"message": "test"})
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTH_MISSING"

    def test_invalid_api_key_returns_403(self):
        """Invalid API key should return 403."""
        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": "wrong-key"},
            json={"message": "test"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "AUTH_INVALID"

    def test_valid_api_key_returns_200(self):
        """Valid API key should work."""
        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "This is a test"},
        )
        assert response.status_code == 200


class TestScamDetection:
    """Test scam detection accuracy."""

    def test_digital_arrest_scam_detected(self):
        """Digital arrest scam should be detected."""
        message = (
            "This is Inspector Raj Sharma from CBI Mumbai. "
            "Your Aadhaar card has been used in money laundering case. "
            "You will be arrested in 2 hours unless you cooperate. "
            "Transfer ₹50,000 to account 1234567890123456 IFSC SBIN0001234. "
            "Call me immediately on +919876543210."
        )

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        TestSchemaConsistency()._validate_response_structure(data)

        # Check detection
        assert data["scam_detection"]["is_scam"] == True
        assert data["scam_detection"]["confidence"] > 0.5

        # Check extraction
        intel = data["extracted_intelligence"]
        assert len(intel["bank_accounts"]) > 0
        assert len(intel["phone_numbers"]) > 0
        assert intel["scammer_identity"] is not None

    def test_upi_fraud_detected(self):
        """UPI fraud should be detected."""
        message = (
            "I am from Paytm Customer Care. "
            "There is an issue with your account. "
            "Send ₹1 to verify@paytm for KYC verification. "
            "If you don't verify within 30 minutes, your account will be blocked."
        )

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        TestSchemaConsistency()._validate_response_structure(data)

        assert data["scam_detection"]["is_scam"] == True
        assert len(data["extracted_intelligence"]["upi_ids"]) > 0

    def test_job_scam_detected(self):
        """Job scam should be detected."""
        message = (
            "Congratulations! You have been selected for Data Entry job at Amazon. "
            "Salary ₹25000/month. Work from home. "
            "To complete registration, pay ₹999 for training materials. "
            "Send money to account 112233445566 IFSC HDFC0001234. "
            "Contact hr@amazon-jobs.in"
        )

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        TestSchemaConsistency()._validate_response_structure(data)

        assert data["scam_detection"]["is_scam"] == True
        assert len(data["extracted_intelligence"]["bank_accounts"]) > 0
        assert len(data["extracted_intelligence"]["emails"]) > 0

    def test_non_scam_message(self):
        """Non-scam message should be identified as safe."""
        message = "Hi, I saw your product listing. Can you tell me the price and availability? Thanks!"

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        TestSchemaConsistency()._validate_response_structure(data)

        assert data["scam_detection"]["is_scam"] == False
        assert data["honeypot_response"]["message"] is None
        assert data["conversation_state"]["status"] == "SAFE"


class TestExtraction:
    """Test intelligence extraction."""

    def test_bank_account_extraction(self):
        """Bank account numbers should be extracted."""
        message = "Send money to account 1234567890123456 IFSC code SBIN0001234"

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        accounts = data["extracted_intelligence"]["bank_accounts"]
        assert len(accounts) > 0
        assert accounts[0]["account_number"] == "1234567890123456"
        assert accounts[0]["ifsc_code"] == "SBIN0001234"

    def test_upi_id_extraction(self):
        """UPI IDs should be extracted."""
        message = "My UPI ID is fraudster@ybl for payment"

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        upis = data["extracted_intelligence"]["upi_ids"]
        assert len(upis) > 0
        assert "fraudster@ybl" in [u["upi_id"] for u in upis]

    def test_phone_extraction(self):
        """Phone numbers should be extracted."""
        message = "Call me on +919876543210 for details"

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        phones = data["extracted_intelligence"]["phone_numbers"]
        assert len(phones) > 0
        assert "+919876543210" in [p["number"] for p in phones]


class TestSessionManagement:
    """Test multi-turn session support."""

    def test_session_creation(self):
        """New session should be created without session_id."""
        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "Test message"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert len(data["session_id"]) > 0
        assert data["engagement_metrics"]["turn_number"] == 1

    def test_session_continuation(self):
        """Existing session should continue with session_id."""
        # First message
        response1 = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "First message"},
        )

        session_id = response1.json()["session_id"]

        # Second message with session_id
        response2 = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "session_id": session_id,
                "message": "Second message",
                "conversation_history": [
                    {"role": "scammer", "content": "First message"},
                    {"role": "honeypot", "content": "Response to first"},
                ],
            },
        )

        assert response2.status_code == 200
        data = response2.json()

        assert data["session_id"] == session_id
        assert data["engagement_metrics"]["turn_number"] == 2


class TestPerformance:
    """Test performance requirements."""

    def test_response_time_under_3_seconds(self):
        """Response should be under 3 seconds."""
        message = "This is a test scam message with account 123456789012 and phone +919876543210"

        start_time = time.time()
        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 3.0, (
            f"Response took {end_time - start_time}s, expected < 3s"
        )

    def test_json_validity(self):
        """Response should be valid JSON."""
        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "Test"},
        )

        # Should not raise JSONDecodeError
        data = response.json()
        assert isinstance(data, dict)


class TestFallbackBehavior:
    """Test behavior when components fail."""

    def test_graceful_degradation(self):
        """System should work even with degraded components."""
        # This tests that the system doesn't crash
        # when extraction returns empty or LLM is slow
        message = "Short test"

        response = client.post(
            "/api/v1/honeypot",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": message},
        )

        assert response.status_code == 200
        data = response.json()

        # Should still return valid structure even if extraction is empty
        TestSchemaConsistency()._validate_response_structure(data)


def run_all_tests():
    """Run all tests and print results."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE HONEYPOT API VALIDATION")
    print("=" * 60 + "\n")

    # Run pytest
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {exit_code})")
    print("=" * 60 + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())
