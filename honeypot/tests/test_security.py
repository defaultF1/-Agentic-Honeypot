import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
from honeypot.app.main import app

# Create test client
client = TestClient(app)

@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    with patch("honeypot.app.main.settings") as mock_settings:
        mock_settings.api_key = "test-api-key"
        mock_settings.disable_delays = True
        mock_settings.gemini_api_key = None # Disable LLM for these tests
        mock_settings.rate_limit_requests = 100
        mock_settings.rate_limit_window_seconds = 60
        yield mock_settings

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter to always allow."""
    with patch("honeypot.app.main.rate_limiter") as mock:
        mock.is_allowed.return_value = True
        yield mock

def test_auth_missing(mock_settings, mock_rate_limiter):
    """Test response when API key is missing."""
    response = client.post("/api/v1/honeypot", json={"message": "hello"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_MISSING"

def test_auth_invalid(mock_settings, mock_rate_limiter):
    """Test response when API key is invalid."""
    response = client.post(
        "/api/v1/honeypot",
        json={"message": "hello"},
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_INVALID"

def test_auth_valid(mock_settings, mock_rate_limiter):
    """Test response when API key is valid."""
    # We mock LLM so it goes to fallback logic which should return 200
    with patch("honeypot.app.main.llm_client", None):
        response = client.post(
            "/api/v1/honeypot",
            json={
                "session_id": "test-session",
                "message": "Hello, I am calling from CBI."
            },
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 200
        # Check basic response structure
        data = response.json()
        assert "scam_detection" in data

def test_cors_allowed_origin():
    """Test explicitly allowed origin."""
    origin = "https://huggingface.co"
    response = client.options(
        "/api/v1/honeypot",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key"
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin

def test_cors_regex_allowed_origin():
    """Test regex allowed origins (wildcards)."""
    origins = [
        "https://sub.hf.space",
        "https://another.sub.hf.space",
        "https://foo.guvi.in",
        "https://test.guvi.in",
        "https://hf.space", # Matches regex https://.*\.hf\.space because of .*? No, .* requires at least 0 chars.
        # Original regex: r"https://.*\.hf\.space|https://.*\.guvi\.in"
        # . matches any char. * is zero or more. \. is literal dot.
        # "https://hf.space" -> does not match "https://.*\.hf\.space" unless there is something before .hf.space?
        # Wait, regex is: https://.*\.hf\.space
        # It expects "https://" followed by anything, followed by ".hf.space".
        # So "https://hf.space" might NOT match if ".*" needs to match something?
        # No, .* matches empty string.
        # "https://.hf.space" would match.
        # "https://abc.hf.space" would match.
        # But "https://hf.space" has no dot before hf.space in the regex.
        # The regex is "https://.*\.hf\.space"
        # The literal dot is AFTER .*.
        # So "https://hf.space" is not matched by "https://.*\.hf\.space".
        # Because we need a dot before "hf.space".
        # Let's test checking subdomains as intended.
    ]

    for origin in origins:
        # Note: 'https://hf.space' likely fails with current regex if it strictly requires a dot.
        # "https://foo.hf.space" matches.
        if origin == "https://hf.space":
            # Skip testing strictly root domain if regex implies subdomains, unless we want to verify it fails?
            continue

        response = client.options(
            "/api/v1/honeypot",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key"
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

def test_cors_disallowed_origin():
    """Test disallowed origin."""
    origin = "https://evil.com"
    response = client.options(
        "/api/v1/honeypot",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key"
        }
    )
    # If disallowed, allow-origin header is missing
    assert "access-control-allow-origin" not in response.headers
